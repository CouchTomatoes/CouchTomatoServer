// Home -> Snatched & Available: Cards / Table / Classic (Settings -> Screens, or the switch next to the title).
// Classic is today's MovieList, untouched. Cards and Table are drawn from the same movies the MovieList loaded
// (one row per movie: its newest active release), so nothing is fetched twice; only the live % comes from
// download.watch. Reuses the Activity page's styles and ActivityHelpers.state for the pills and the bar.
// No "Mark as done" here: that button deletes the movie (memory mark-as-done-deletes-movies).

var SnatchedStyle = [
	'.movies > h2 .sv-seg{display:inline-flex;vertical-align:middle;margin-left:12px;border:1px solid #e2e2e2;border-radius:4px;overflow:hidden;font-size:12px;font-weight:400;line-height:normal}',
	'.dark .movies > h2 .sv-seg{border-color:#404040}',
	'.movies > h2 .sv-seg button{border:0;background:transparent;color:inherit;opacity:.75;font:inherit;padding:4px 9px;cursor:pointer;white-space:nowrap}',
	'.movies > h2 .sv-seg button.on{background:#ac0000;color:#fff;opacity:1}',
	'.dark .movies > h2 .sv-seg button.on{background:#f85c22}',
	'.act.sv{padding:4px 0 8px}',
	'.act.sv:empty{display:none}',
	'.act.sv .card{position:relative;align-items:flex-start}',
	'.act.sv .card .rn{font-size:12.5px;color:var(--muted);margin-top:2px;overflow-wrap:anywhere}',
	'.act.sv .card .chead{padding-right:150px}',
	'.act.sv .card .chead .pill{position:absolute;top:12px;right:12px}',
	'.act.sv .card .bar{margin:8px 0}',
	'.act.sv .card .btns{margin-top:4px}',
	'.act.sv td .rn{font-size:12.5px;color:var(--muted);margin-top:2px;overflow-wrap:anywhere}',
	'.act.sv .ic{min-width:34px;text-align:center;padding:6px 8px}',
	'.act.sv .btn.dl{border-color:var(--acc);color:var(--acc)}',
	'.act.sv td.c-act .btns{flex-wrap:nowrap}',
	'.hv-v-dashboard .scroll_content > .movies.sv-on{grid-column:1/-1}',  // Dashboard: full row, not one narrow card
	'.hv-v-dashboard .act.sv .card{background:var(--bg)}',
	'.movies.sv-on > .hv-more{display:none}',
	'@media (max-width:600px){',
	'.act.sv .card .chead{padding-right:0}',
	'.act.sv .card .chead .pill{position:static}',
	'.act.sv td.c-num{display:none}',
	'}'
].join('');

var SnatchedViews = new Class({

	ACTIVE: ['snatched', 'downloaded', 'missing', 'seeding'],
	SHOWN: ['snatched', 'downloaded', 'missing', 'seeding', 'available', 'done'],

	initialize: function(list){
		var self = this;
		self.list = list;
		self.live = {};
		self.view = (App.getOption('screens') || {}).snatched_view || 'classic';

		ActivityHelpers.style();
		if(!SnatchedViews.styled){
			SnatchedViews.styled = true;
			new Element('style#snatched_style', {'type': 'text/css', 'text': SnatchedStyle}).inject(document.head);
		}

		var el = $(list);
		self.body = new Element('div.act.sv').inject(list.movie_list, 'before');  // movie_list stays the last child

		if(list.title){
			self.seg = new Element('span.sv-seg').inject(list.title);
			[['cards', '▦ Cards'], ['table', '≡ Table'], ['classic', '↺ Classic']].each(function(v){
				new Element('button', {
					'type': 'button', 'text': v[1], 'data-view': v[0],
					'events': {'click': function(e){ (e).stop(); self.pickView(v[0]); }}
				}).inject(self.seg);
			});
		}

		list.addEvent('loaded', function(){ self.render(); self.watch(); });
		App.on('release.progress', function(notification){
			if(self.view == 'classic' || !el.getParent('.page.active')) return;
			self.takeLive(notification.data);
			self.render();
		});

		self.apply();
	},

	pickView: function(view){
		var self = this;
		if(self.view == view) return;
		self.view = view;
		self.apply();
		self.watch();

		// Same setting as Settings -> Screens, so the choice sticks on every browser
		var screens = App.getOption('screens');
		if(screens) screens.snatched_view = view;
		Api.request('settings.save', {'data': {'section': 'screens', 'name': 'snatched_view', 'value': view}});
	},

	apply: function(){
		var self = this, classic = self.view == 'classic';
		$(self.list)[classic ? 'removeClass' : 'addClass']('sv-on');
		self.list.movie_list.setStyle('display', classic ? '' : 'none');
		if(self.seg) self.seg.getElements('button').each(function(b){
			b[b.get('data-view') == self.view ? 'addClass' : 'removeClass']('on');
		});
		self.render();
	},

	// One row per movie: its newest active release, else its newest available / done one
	rows: function(){
		var self = this, now = Math.floor(Date.now() / 1000), out = [];
		(self.list.movies || []).each(function(m){
			var movie = m.data || m, best = null;
			(movie.releases || []).each(function(rel){
				if(self.SHOWN.indexOf(rel.status) < 0) return;
				var rank = self.ACTIVE.indexOf(rel.status) > -1 ? 1 : 0;
				if(!best || rank > best.rank || (rank == best.rank && (rel.last_edit || 0) > (best.rel.last_edit || 0)))
					best = {'rel': rel, 'rank': rank};
			});
			if(best) out.push({'movie': movie, 'rel': best.rel, 'st': self.state(best.rel, now)});
		});
		return out;
	},

	state: function(rel, now){
		if(rel.status == 'available') return {'k': 'avail', 'label': 'Available', 'pct': null, 'cls': 'ok'};
		if(rel.status == 'done') return {'k': 'lib', 'label': 'In library', 'pct': 100, 'cls': 'ok'};
		if(rel.status == 'seeding') return {'k': 'seed', 'label': 'Seeding', 'pct': 100, 'cls': 'ok'};
		var st = ActivityHelpers.state(rel, this.live[rel._id], now);
		if(st.k == 'stuck') st.label = 'Stuck · 0 peers';
		st.cls = {'dl': 'dl', 'wait': 'wait', 'done': 'ok', 'failed': 'bad', 'gone': 'bad'}[st.k] || 'blk';
		return st;
	},

	// Ask the downloader for the % of the snatched ones (the server answers from its live cache)
	watch: function(){
		var self = this;
		if(self.view == 'classic' || document.hidden) return;
		var ids = [];
		self.rows().each(function(r){
			if(['snatched', 'downloaded'].indexOf(r.rel.status) > -1 && ids.indexOf(r.movie._id) < 0) ids.push(r.movie._id);
		});
		if(!ids.length) return;
		Api.request('download.watch', {
			'data': {'media_id': ids.join(',')},
			'onComplete': function(json){
				if(!json || !json.success) return;
				self.takeLive(json.releases);
				self.render();
			}
		});
	},

	takeLive: function(items){
		var self = this;
		(items || []).each(function(item){ self.live[item.release_id] = item; });
	},

	render: function(){
		var self = this;
		self.body.empty();
		if(self.view == 'classic') return;

		var rows = self.rows();
		if(!rows.length) return;  // the MovieList shows its own empty message

		// Problems first, then newest first
		rows.sort(function(a, b){
			var pa = a.st.blocked ? 1 : 0, pb = b.st.blocked ? 1 : 0;
			if(pa != pb) return pb - pa;
			return (b.rel.last_edit || 0) - (a.rel.last_edit || 0);
		});

		if(self.view == 'table') self.renderTable(rows);
		else rows.each(function(r){ self.body.grab(self.card(r)); });
	},

	card: function(r){
		var self = this, st = r.st, info = r.rel.info || {},
			poster = ActivityHelpers.poster(r.movie);

		return new Element('div.card' + (st.blocked ? '.blk' : '')).adopt(
			new Element('div.poster', poster ? {'styles': {'background-image': 'url(' + poster + ')'}} : {}),
			new Element('div.cbody').adopt(
				new Element('div.chead').adopt(
					new Element('span.t', {'text': self.title(r.movie)}),
					new Element('span.pill.' + st.cls, {'text': st.label + (st.k == 'dl' ? ' ' + st.pct + '%' : '')})
				),
				info.name ? new Element('div.rn', {'text': info.name}) : null,
				new Element('div.meta', {'text': self.meta(r)}),
				st.pct != null ? new Element('div.bar' + (st.blocked ? '.blk' : (st.cls == 'ok' ? '.ok' : ''))).grab(
					new Element('i', {'styles': {'width': Math.max(st.pct, st.blocked ? 4 : 0) + '%'}})) : null,
				st.why ? new Element('div.warn', {'text': '⚠ ' + st.why}) : null,
				self.buttons(r, false)
			)
		);
	},

	renderTable: function(rows){
		var self = this, tbody = new Element('tbody');
		rows.each(function(r){
			var info = r.rel.info || {}, st = r.st;
			tbody.grab(new Element('tr').adopt(
				new Element('td.c-movie').adopt(
					new Element('div.t', {'text': self.title(r.movie)}),
					info.name ? new Element('div.rn', {'text': info.name}) : null,
					st.why ? new Element('div.warn', {'text': '⚠ ' + st.why}) : null
				),
				new Element('td.c-status').grab(new Element('span.pill.' + st.cls, {'text': st.label + (st.k == 'dl' ? ' ' + st.pct + '%' : '')})),
				new Element('td.c-num', {'text': ActivityHelpers.quality(r.rel.quality) || '—'}),
				new Element('td.c-num', {'text': self.size(info.size)}),
				new Element('td.c-num', {'text': info.age != null && info.age !== '' ? Math.round(info.age) + ' d' : '—'}),
				new Element('td.c-num', {'text': info.score != null ? info.score : '—'}),
				new Element('td.c-num', {'text': info.provider || '—'}),
				new Element('td.c-act').grab(self.buttons(r, true))
			));
		});

		self.body.grab(new Element('table').adopt(
			new Element('thead').grab(new Element('tr').adopt(
				['Release', 'Status', 'Quality', 'Size', 'Age', 'Score', 'Provider', ''].map(function(h, nr){
					return new Element('th' + (nr > 1 && nr < 7 ? '.c-num' : ''), {'text': h});
				})
			)),
			tbody
		));
	},

	// ----- Pieces -----

	title: function(movie){
		return ActivityHelpers.title(movie) + (movie.info && movie.info.year ? ' (' + movie.info.year + ')' : '');
	},

	size: function(mb){
		mb = parseFloat(mb);
		if(!mb) return '—';
		return mb >= 1024 ? (mb / 1024).toFixed(1) + ' GB' : Math.round(mb) + ' MB';
	},

	meta: function(r){
		var info = r.rel.info || {};
		return [ActivityHelpers.quality(r.rel.quality), info.size ? this.size(info.size) : null, info.provider]
			.filter(function(x){ return x; }).join(' · ');
	},

	// Try next release (problems only), Download again, Ignore release, Details. compact = the table's ⤓ / ✕.
	buttons: function(r, compact){
		var self = this, box = new Element('div.btns'), rel = r.rel, info = rel.info || {};

		var busy = function(text){ box.empty().grab(new Element('span.pct', {'text': text})); };
		var reload = function(){ self.list.update(); };

		if(r.st.blocked && !compact)
			new Element('button.btn.solid', {'type': 'button', 'text': 'Try next release', 'events': {'click': function(e){
				(e).stop(); busy('Searching for another release…');
				Api.request('movie.searcher.try_next', {'data': {'media_id': r.movie._id}, 'onComplete': reload});
			}}}).inject(box);

		if(info.url || info.id)
			new Element('button.btn.dl' + (compact ? '.ic' : ''), {
				'type': 'button',
				'text': compact ? '⤓' : '⤓ ' + (rel.status == 'available' ? 'Download' : 'Download again'),
				'title': 'Send this release to your downloader' + (rel.status == 'available' ? '' : ' again'),
				'events': {'click': function(e){
					(e).stop(); busy('Sending to the downloader…');
					Api.request('release.manual_download', {'data': {'id': rel._id}, 'onComplete': reload});
				}}
			}).inject(box);

		if(rel.status != 'done')
			new Element('button.btn' + (compact ? '.ic' : ''), {
				'type': 'button',
				'text': compact ? '✕' : 'Ignore release',
				'title': 'Ignore this release: it will not be downloaded again',
				'events': {'click': function(e){
					(e).stop(); busy('Ignoring…');
					Api.request('release.ignore', {'data': {'id': rel._id}, 'onComplete': reload});
				}}
			}).inject(box);

		if(!compact)
			new Element('button.btn', {'type': 'button', 'text': 'Details ›', 'events': {'click': function(e){
				(e).stop(); Page.Activity.prototype.openDetails(r.movie);
			}}}).inject(box);

		return box;
	}
});
