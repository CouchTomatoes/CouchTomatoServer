// Activity page: every snatched download right now, live from the downloader, and the ones that need you.
// Two views (Settings -> Screens -> Activity, or the switch top right): Table (Queue / Blocked tabs) and Cards
// (Needs you / Downloading). Nothing here is stored: rows come from media.list, % and time left from the
// in-memory live status (download_live.py), refreshed every 10 s while this page is open.
// Styles live here (injected once) because the Sass build is not part of tools/jsbuild.

var ActivityStyle = [
	'.page.activity .scroll_content{padding:0 20px 40px}',
	'.act{--line:#e2e2e2;--muted:#6a6a6a;--card:#ebebeb;--bg:#fff;--text:#000;--acc:#ac0000;--bar:#e6e6e6;',
	'--dl:#1f5f9e;--dl-bg:#e1eefb;--warn:#8a5a00;--warn-bg:#fff1d6;--ok:#1d7a3a;--ok-bg:#e3f5e8;--bad:#c4002f;--bad-bg:#ffe4ea}',
	'.dark .act{--line:#404040;--muted:#a8a8a8;--card:#363636;--bg:#2d2d2d;--text:#fff;--acc:#f85c22;--bar:#4a4a4a;',
	'--dl:#8cc0ef;--dl-bg:#233648;--warn:#ffc266;--warn-bg:#4a3a1c;--ok:#6ad68b;--ok-bg:#20402a;--bad:#ff7d99;--bad-bg:#4d2230}',
	'.act .act_top{display:flex;flex-wrap:wrap;align-items:center;gap:10px 14px;padding:20px 0 14px;border-bottom:1px solid var(--line);margin-bottom:14px}',
	'.act .act_top h2{font-weight:300;font-size:24px;margin:0}',
	'.act .sub{font-size:12.5px;color:var(--muted)}',
	'.act .need{font-size:11.5px;font-weight:700;color:var(--warn);background:var(--warn-bg);border-radius:3px;padding:2px 7px}',
	'.act .seg{display:inline-flex;margin-left:auto;border:1px solid var(--line);border-radius:4px;overflow:hidden;background:var(--bg)}',
	'.act .seg button{border:0;background:transparent;color:var(--muted);font:inherit;font-size:12px;padding:5px 10px;cursor:pointer;white-space:nowrap}',
	'.act .seg button.on{background:var(--acc);color:#fff}',
	'.act .tabs{display:flex;gap:4px;border-bottom:1px solid var(--line);margin-bottom:4px}',
	'.act .tabs a{padding:8px 14px;font-size:14px;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px}',
	'.act .tabs a.on{color:var(--text);font-weight:600;border-bottom-color:var(--acc)}',
	'.act table{width:100%;border-collapse:collapse}',
	'.act th{text-align:left;font-size:11.5px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);padding:10px 8px;border-bottom:1px solid var(--line)}',
	'.act td{padding:10px 8px;border-bottom:1px solid var(--line);vertical-align:middle;font-size:14px}',
	'.act .t{font-weight:600}',
	'.act .meta{font-size:12.5px;color:var(--muted);margin-top:2px}',
	'.act .warn{font-size:12.5px;color:var(--warn);margin-top:2px}',
	'.act .pill{display:inline-block;font-size:11.5px;font-weight:600;border-radius:3px;padding:2px 7px;white-space:nowrap}',
	'.act .pill.dl{color:var(--dl);background:var(--dl-bg)}',
	'.act .pill.wait{color:var(--muted);background:var(--card)}',
	'.act .pill.ok{color:var(--ok);background:var(--ok-bg)}',
	'.act .pill.blk{color:var(--warn);background:var(--warn-bg)}',
	'.act .pill.bad{color:var(--bad);background:var(--bad-bg)}',
	'.act .bar{height:6px;border-radius:3px;background:var(--bar);overflow:hidden;max-width:160px}',
	'.act .bar i{display:block;height:100%;background:var(--acc)}',
	'.act .bar.blk i{background:var(--warn)}',
	'.act .bar.ok i{background:var(--ok)}',
	'.act .pct{font-size:12.5px;color:var(--muted);margin-top:3px}',
	'.act .btn{display:inline-block;border:1px solid var(--line);background:var(--bg);color:var(--text);border-radius:3px;padding:6px 12px;font:inherit;font-size:13px;cursor:pointer;white-space:nowrap}',
	'.act .btn.fix{border-color:var(--acc);color:var(--acc)}',
	'.act .btn.solid{background:var(--acc);border-color:var(--acc);color:#fff}',
	'.act .btns{display:flex;flex-wrap:wrap;gap:6px}',
	'.act .empty{padding:30px 0;color:var(--muted);font-size:14px}',
	'.act .foot{font-size:12.5px;color:var(--muted);margin-top:14px}',
	'.act h3{font-size:12px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--muted);margin:16px 0 8px}',
	'.act .card{display:flex;gap:12px;background:var(--card);border-radius:4px;padding:12px;margin-bottom:10px}',
	'.act .card.blk{border-left:3px solid var(--warn)}',
	'.act .card .poster{flex:none;width:56px;height:84px;border-radius:3px;background:var(--bar) center/cover no-repeat}',
	'.act .card .cbody{flex:1 1 auto;min-width:0}',
	'.act .card .chead{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline}',
	'.act .card .chead .meta{margin-left:auto}',
	'.act .steps{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:8px 0}',
	'.act .steps .s{font-size:12px;border-radius:12px;padding:3px 9px;color:var(--ok);background:var(--ok-bg)}',
	'.act .steps .s.now{background:var(--acc);color:#fff;font-weight:600}',
	'.act .steps .s.now.blk{background:var(--warn);color:#fff}',
	'.act .steps .s.next{background:transparent;color:var(--muted)}',
	'.act .steps .ln{width:14px;height:1px;background:var(--line)}',
	'.act .card .bar{max-width:none;margin:4px 0}',
	'@media (max-width:600px){',
	'.act thead{display:none}',
	'.act tr{display:grid;grid-template-columns:1fr auto;gap:6px 10px;padding:10px 0;border-bottom:1px solid var(--line)}',
	'.act td{border:0;padding:0}',
	'.act td.c-movie{grid-column:1/-1}',
	'.act td.c-prog{grid-column:1/-1}',
	'.act .bar{max-width:none}',
	'.act .card .poster{width:44px;height:66px}',
	'}'
].join('');

var ActivityHelpers = {

	STUCK_AFTER: 6 * 3600,   // snatched this long with 0 % = stuck
	IMPORT_AFTER: 30 * 60,   // finished this long ago and still not in the library = can't import

	style: function(){
		if(ActivityHelpers.styled) return;
		ActivityHelpers.styled = true;
		new Element('style#activity_style', {'type': 'text/css', 'text': ActivityStyle}).inject(document.head);
	},

	ago: function(seconds){
		if(seconds < 3600) return Math.max(1, Math.round(seconds / 60)) + ' min';
		if(seconds < 172800) return Math.round(seconds / 3600) + ' hours';
		return Math.round(seconds / 86400) + ' days';
	},

	eta: function(seconds){
		if(seconds == null || seconds < 0) return '—';
		if(seconds < 60) return 'under 1 min';
		var h = Math.floor(seconds / 3600), m = Math.round((seconds % 3600) / 60);
		if(m == 60){ h += 1; m = 0; }
		return h ? h + ' h ' + m + ' m' : m + ' min';
	},

	quality: function(q){
		if(!q) return null;
		var found = window.Quality ? Quality.getQuality(q) : {};
		return (found && found.label) || q;
	},

	poster: function(movie){
		var files = movie.files || {}, images = (movie.info || {}).images || {};
		if(files.image_poster && files.image_poster.length)
			return Api.createUrl('file.cache') + files.image_poster[0].split(Api.getOption('path_sep')).pop();
		if(images.poster && images.poster.length) return images.poster[0];
		return null;
	},

	title: function(movie){
		var info = movie.info || {};
		return movie.title || (info.titles && info.titles[0]) || 'Unknown movie';
	},

	// What a snatched release is doing now. live = its download.live item, or undefined when the
	// downloader hasn't answered for it (yet).
	state: function(rel, live, now){
		var age = now - ((live && live.added) || rel.last_edit || now),
			pct = live && live.progress != null ? Math.round(live.progress) : (rel.status == 'downloaded' ? 100 : null);

		if(rel.status == 'missing')
			return {'k': 'gone', 'label': 'Gone', 'blocked': true, 'pct': pct,
				'why': 'The downloader no longer has this download. It was removed or never started.'};
		if(live && live.status == 'failed')
			return {'k': 'failed', 'label': 'Failed', 'blocked': true, 'pct': pct,
				'why': 'The downloader says this download failed.'};
		if(pct == 100 && rel.status == 'snatched' && live && live.done && now - live.done > ActivityHelpers.IMPORT_AFTER)
			return {'k': 'noimport', 'label': "Can't import", 'blocked': true, 'pct': 100,
				'why': 'Finished ' + ActivityHelpers.ago(now - live.done) + ' ago but not moved to your library. The renamer may have found no usable video file.'};
		if(pct == 100 || rel.status == 'downloaded')
			return {'k': 'done', 'label': 'Downloaded', 'pct': 100, 'why': null};
		if(pct === 0 && age > ActivityHelpers.STUCK_AFTER)
			return {'k': 'stuck', 'label': 'Stuck', 'blocked': true, 'pct': 0,
				'why': 'Nothing downloaded in ' + ActivityHelpers.ago(age) + '. No one may be sharing this file.'};
		if(pct == null)
			return {'k': 'wait', 'label': 'Snatched', 'pct': null, 'why': null};
		return {'k': 'dl', 'label': 'Downloading', 'pct': pct, 'why': null};
	}
};

Page.Activity = new Class({

	Extends: PageBase,

	order: 4,
	name: 'activity',
	title: 'What is downloading now',
	icon: 'download',

	list_tab: 'queue',  // not 'tab': PageBase keeps its menu tab element in self.tab

	indexAction: function(){
		var self = this;
		ActivityHelpers.style();

		if(!self.el_wrap){
			self.view = (App.getOption('screens') || {}).activity_view || 'table';
			self.live = {};
			self.waived = {};

			self.el_wrap = new Element('div.act').adopt(
				new Element('div.act_top').adopt(
					new Element('h2', {'text': 'Activity'}),
					self.sub = new Element('span.sub'),
					self.seg = new Element('div.seg')
				),
				self.body = new Element('div'),
				new Element('div.foot', {'text': 'Read live from your downloader every 10 s. Nothing here is stored. Finished movies move to History.'})
			).inject(self.content);

			[['table', '≡ Table'], ['cards', '▦ Cards']].each(function(v){
				new Element('button', {
					'type': 'button', 'text': v[1], 'data-view': v[0],
					'events': {'click': function(){ self.pickView(v[0]); }}
				}).inject(self.seg);
			});
			self.markView();

			App.on('release.progress', function(notification){
				if(!self.el.hasClass('active')) return;
				self.takeLive(notification.data);
				self.render();
			});
			App.on('release.update_status', function(){
				if(self.el.hasClass('active')) self.loadRows();
			});
			document.addEventListener('visibilitychange', function(){
				if(!document.hidden && self.el.hasClass('active')) self.watch();
			});
		}

		self.loadRows();
		clearInterval(self.timer);
		self.timer = setInterval(function(){
			if(!self.el.hasClass('active')){ clearInterval(self.timer); return; }
			self.watch();
		}, 15000);
	},

	pickView: function(view){
		var self = this;
		if(self.view == view) return;
		self.view = view;
		self.markView();
		self.render();

		// Same setting as Settings -> Screens, so the choice sticks on every browser
		var screens = App.getOption('screens');
		if(screens) screens.activity_view = view;
		Api.request('settings.save', {'data': {'section': 'screens', 'name': 'activity_view', 'value': view}});
	},

	markView: function(){
		var self = this;
		self.seg.getElements('button').each(function(b){
			b[b.get('data-view') == self.view ? 'addClass' : 'removeClass']('on');
		});
	},

	// Not load(): PageBase.load() builds the menu tab (memory pagebase-load-override)
	loadRows: function(){
		var self = this;
		if(self.request && self.request.running) self.request.cancel();
		self.request = Api.request('media.list', {
			'data': {'type': 'movie', 'release_status': 'snatched,downloaded,missing'},
			'onComplete': function(json){
				self.rows = [];
				((json && json.movies) || []).each(function(movie){
					(movie.releases || []).each(function(rel){
						if(['snatched', 'downloaded', 'missing'].indexOf(rel.status) > -1)
							self.rows.push({'movie': movie, 'rel': rel});
					});
				});
				self.loaded = !!(json && json.success);
				self.render();
				self.watch();
			}
		});
	},

	// Tell the server we're looking (its 10 s fast lane runs only while someone is) and take what it knows
	watch: function(){
		var self = this;
		if(document.hidden || !self.rows || !self.rows.length) return;
		var ids = self.rows.map(function(r){ return r.movie._id; }).unique();
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

	rowsWithState: function(){
		var self = this, now = Math.floor(Date.now() / 1000);
		return (self.rows || []).map(function(r){
			var st = ActivityHelpers.state(r.rel, self.live[r.rel._id], now);
			if(st.blocked && self.waived[r.rel._id]) st = {'k': 'wait', 'label': 'Waiting', 'pct': st.pct, 'why': null};
			return {'movie': r.movie, 'rel': r.rel, 'st': st, 'live': self.live[r.rel._id] || {}};
		});
	},

	render: function(){
		var self = this;
		if(!self.body) return;
		self.body.empty();

		var rows = self.rowsWithState(),
			blocked = rows.filter(function(r){ return r.st.blocked; }),
			queue = rows.filter(function(r){ return !r.st.blocked; });

		self.sub.empty();
		if(blocked.length) self.sub.grab(new Element('span.need', {'text': blocked.length + ' need' + (blocked.length == 1 ? 's' : '') + ' you'}));
		else if(rows.length) self.sub.set('text', queue.length + ' download' + (queue.length == 1 ? '' : 's'));

		if(self.loaded === false){
			self.body.grab(new Element('div.empty', {'text': 'Could not load your downloads.'}));
			return;
		}
		if(!rows.length){
			self.body.grab(new Element('div.empty', {'text': 'Nothing is downloading. Snatched movies show up here until they reach your library.'}));
			return;
		}

		if(self.view == 'cards') self.renderCards(queue, blocked);
		else self.renderTable(queue, blocked);
	},

	// ----- Table -----

	renderTable: function(queue, blocked){
		var self = this;
		if(self.list_tab == 'blocked' && !blocked.length) self.list_tab = 'queue';

		var tabs = new Element('div.tabs');
		[['queue', 'Queue', queue.length], ['blocked', 'Blocked', blocked.length]].each(function(t){
			new Element('a' + (self.list_tab == t[0] ? '.on' : ''), {
				'text': t[1] + ' (' + t[2] + ')',
				'events': {'click': function(){ self.list_tab = t[0]; self.render(); }}
			}).inject(tabs);
		});

		var list = self.list_tab == 'blocked' ? blocked : queue,
			tbody = new Element('tbody');
		list.each(function(r){ tbody.grab(self.tableRow(r)); });

		self.body.adopt(
			tabs,
			list.length ? new Element('table').adopt(
				new Element('thead').grab(new Element('tr').adopt(
					['Movie', 'Status', 'Progress', 'Left', ''].map(function(h){ return new Element('th', {'text': h}); })
				)),
				tbody
			) : new Element('div.empty', {'text': 'Nothing here.'})
		);
	},

	tableRow: function(r){
		var self = this, st = r.st;
		return new Element('tr').adopt(
			new Element('td.c-movie').adopt(
				new Element('div.t', {'text': ActivityHelpers.title(r.movie) + (r.movie.info && r.movie.info.year ? ' (' + r.movie.info.year + ')' : '')}),
				new Element('div.meta', {'text': self.metaText(r)}),
				st.why ? new Element('div.warn', {'text': '⚠ ' + st.why}) : null
			),
			new Element('td.c-status').grab(self.pill(st)),
			new Element('td.c-prog').adopt(self.bar(st)),
			new Element('td.c-left', {'text': st.k == 'dl' ? ActivityHelpers.eta(r.live.eta) : '—'}),
			new Element('td.c-act').grab(self.actions(r, false))
		);
	},

	// ----- Cards -----

	renderCards: function(queue, blocked){
		var self = this;
		if(blocked.length){
			self.body.grab(new Element('h3', {'text': 'Needs you'}));
			blocked.each(function(r){ self.body.grab(self.card(r)); });
		}
		if(queue.length){
			self.body.grab(new Element('h3', {'text': 'Downloading'}));
			queue.each(function(r){ self.body.grab(self.card(r)); });
		}
	},

	card: function(r){
		var self = this, st = r.st,
			poster = ActivityHelpers.poster(r.movie),
			steps = new Element('div.steps');

		var chain = [['✓ Wanted', 's'], ['✓ Snatched', 's']];
		if(st.k == 'noimport') chain.push(['✓ Downloaded', 's']);
		chain.push([st.k == 'dl' ? 'Downloading ' + st.pct + '%' : st.label, 's.now' + (st.blocked ? '.blk' : '')]);
		if(!st.blocked) chain.push(['In library', 's.next']);
		chain.each(function(c, nr){
			if(nr) steps.grab(new Element('span.ln'));
			steps.grab(new Element('span.' + c[1], {'text': c[0]}));
		});

		var line = [];
		if(st.pct != null) line.push(st.pct + '%');
		if(st.k == 'dl' && r.live.eta != null) line.push(ActivityHelpers.eta(r.live.eta) + ' left');

		return new Element('div.card' + (st.blocked ? '.blk' : '')).adopt(
			new Element('div.poster', poster ? {'styles': {'background-image': 'url(' + poster + ')'}} : {}),
			new Element('div.cbody').adopt(
				new Element('div.chead').adopt(
					new Element('span.t', {'text': ActivityHelpers.title(r.movie) + (r.movie.info && r.movie.info.year ? ' (' + r.movie.info.year + ')' : '')}),
					new Element('span.meta', {'text': self.metaText(r)})
				),
				steps,
				st.pct != null ? self.bar(st)[0] : null,
				line.length && !st.blocked ? new Element('div.pct', {'text': line.join(' · ')}) : null,
				st.why ? new Element('div.warn', {'text': '⚠ ' + st.why}) : null,
				st.blocked ? self.actions(r, true) : null
			)
		);
	},

	// ----- Pieces -----

	metaText: function(r){
		var bits = [ActivityHelpers.quality(r.rel.quality), (r.rel.info || {}).provider].filter(function(x){ return x; });
		return bits.join(' · ');
	},

	pill: function(st){
		var cls = {'dl': 'dl', 'wait': 'wait', 'done': 'ok', 'failed': 'bad', 'gone': 'bad'}[st.k] || 'blk';
		return new Element('span.pill.' + cls, {'text': st.label});
	},

	bar: function(st){
		if(st.pct == null) return [new Element('div.pct', {'text': 'Waiting for the downloader'})];
		return [
			new Element('div.bar' + (st.blocked ? '.blk' : (st.k == 'done' ? '.ok' : ''))).grab(new Element('i', {'styles': {'width': st.pct + '%'}})),
			new Element('div.pct', {'text': st.pct + '%'})
		];
	},

	// Blocked: Fix… opens the two real choices. Otherwise: Details (no fake cancel; the downloader owns that).
	actions: function(r, open){
		var self = this, box = new Element('div.btns');

		var choices = function(){
			box.empty();
			new Element('button.btn.solid', {'type': 'button', 'text': 'Try another release', 'events': {'click': function(){
				box.empty().grab(new Element('span.pct', {'text': 'Searching for another release…'}));
				Api.request('movie.searcher.try_next', {'data': {'media_id': r.movie._id}, 'onComplete': function(){ self.loadRows(); }});
			}}}).inject(box);
			new Element('button.btn', {'type': 'button', 'text': 'Keep waiting', 'events': {'click': function(){
				self.waived[r.rel._id] = true;
				self.render();
			}}}).inject(box);
		};

		if(r.st.blocked){
			if(open) choices();
			else new Element('button.btn.fix', {'type': 'button', 'text': 'Fix…', 'events': {'click': choices}}).inject(box);
		}
		else
			new Element('button.btn', {'type': 'button', 'text': 'Details', 'events': {'click': function(){ self.openDetails(r.movie); }}}).inject(box);

		return box;
	},

	openDetails: function(movie){
		var stub = {'options': {}, 'calculateSelected': function(){}, 'checkIfEmpty': function(){}},
			m = new Movie(stub, {'actions': [MA.IMDB, MA.Release, MA.Trailer, MA.Refresh, MA.Delete, MA.Category, MA.Profile]}, movie);
		m.openDetails();
	}
});
