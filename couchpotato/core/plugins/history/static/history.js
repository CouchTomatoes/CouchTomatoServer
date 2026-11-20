// History page: a dated timeline, one stop per day, one card per movie chaining that day's steps.
// Styles live here (injected once) because the Sass build is not part of tools/jsbuild.

var HistoryTypes = {
	added: {label: 'Added', k: 'add'},
	snatched: {label: 'Snatched', k: 'snatch'},
	downloaded: {label: 'Downloaded', k: 'done'},
	moved: {label: 'Moved to library', k: 'move'},
	replaced: {label: 'Replaced', k: 'replace'},
	failed: {label: 'Failed', k: 'fail'},
	subtitle: {label: 'Subtitles', k: 'sub'},
	subfail: {label: 'No subtitles', k: 'fail'},
	updated: {label: 'App updated', k: 'sys'},
	rollback: {label: 'Update rolled back', k: 'fail'},
	signin: {label: 'Signed in', k: 'sys'}
};

var HistoryKeep = {'90': '90 days', '365': '1 year', 'forever': 'everything (Forever)'};

var HistoryStyle = [
	'.page.history .scroll_content{padding:0 20px 40px}',
	'.ht{--line:#e2e2e2;--muted:#6a6a6a;--card:#ebebeb;--bg:#fff;--p:#ac0000;',
	'--snatch:#b25d00;--snatch-bg:#fff1e0;--done:#1d7a3a;--done-bg:#e3f5e8;--move:#2f5f8a;--move-bg:#e4eef8;',
	'--replace:#6b3fa0;--replace-bg:#f0e8fa;--fail:#c4002f;--fail-bg:#ffe4ea;--sys:#555;--sys-bg:#e4e4e4;',
	'--sub:#00788a;--sub-bg:#dff4f7;--add:#ac0000;--add-bg:#fde8e8}',
	'.dark .ht{--line:#404040;--muted:#a8a8a8;--card:#363636;--bg:#2d2d2d;--p:#f85c22;',
	'--snatch:#ffb35c;--snatch-bg:#4a3520;--done:#6ad68b;--done-bg:#20402a;--move:#8cc0ef;--move-bg:#233648;',
	'--replace:#c7a4f2;--replace-bg:#3a2c4c;--fail:#ff7d99;--fail-bg:#4d2230;--sys:#cfcfcf;--sys-bg:#4a4a4a;',
	'--sub:#6fd6e6;--sub-bg:#1f4046;--add:#f85c22;--add-bg:#4a2c20}',
	'.ht .ht_top{display:flex;flex-wrap:wrap;align-items:center;gap:10px 16px;padding:20px 0 14px}',
	'.ht .ht_top h2{font-weight:300;font-size:24px;margin:0;flex:1 1 auto}',
	'.ht .chips{display:flex;flex-wrap:wrap;gap:6px}',
	'.ht .chip{font-size:12.5px;background:var(--card);border:1px solid transparent;border-radius:3px;padding:4px 10px;cursor:pointer;color:inherit}',
	'.ht .chip.on{border-color:var(--p);color:var(--p);background:transparent;font-weight:600}',
	'.ht select.range{font:inherit;font-size:13px;color:inherit;background:var(--bg);border:1px solid var(--line);border-radius:3px;padding:5px 8px}',
	'.ht .badge{display:inline-flex;align-items:center;font-size:11.5px;font-weight:600;padding:2px 8px;border-radius:3px;white-space:nowrap}',
	'.ht .q{font-size:11.5px;font-weight:600;border:1px solid var(--line);border-radius:3px;padding:1px 6px;white-space:nowrap}',
	'.ht .muted{color:var(--muted)}',
	'.ht .title{font-weight:600}',
	'.ht .tnum{font-variant-numeric:tabular-nums}',
	'.ht .tday,.ht .gap{display:grid;grid-template-columns:74px 22px minmax(0,1fr)}',
	'.ht .tdate{text-align:right;padding-top:2px;line-height:1.1}',
	'.ht .tdate .dw,.ht .tdate .dm{font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}',
	'.ht .tdate .dn{font-size:26px;font-weight:300}',
	'.ht .rail{position:relative}',
	'.ht .rail:before{content:"";position:absolute;left:50%;top:0;bottom:0;width:2px;margin-left:-1px;background:var(--line)}',
	'.ht .gap .rail:before{background:repeating-linear-gradient(var(--line) 0 4px,transparent 4px 8px)}',
	'.ht .dot{position:absolute;left:50%;top:8px;width:12px;height:12px;margin-left:-6px;border-radius:50%;background:var(--bg);border:2px solid var(--p);box-sizing:border-box}',
	'.ht .dot.fail{border-color:var(--fail);background:var(--fail)}',
	'.ht .dot.sys{border-color:var(--sys)}',
	'.ht .tbody{display:grid;gap:8px;padding:0 0 18px 6px;min-width:0}',
	'.ht .tcard{background:var(--card);border-radius:4px;padding:9px 12px;display:grid;gap:7px}',
	'.ht .tcard.failed{box-shadow:inset 3px 0 0 var(--fail)}',
	'.ht .chead{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline}',
	'.ht .tsteps{display:flex;flex-wrap:wrap;gap:6px 4px;align-items:center;font-size:12px}',
	'.ht .tsteps .st{display:inline-flex;gap:6px;align-items:center}',
	'.ht .tsteps .arr{color:var(--muted);padding:0 2px}',
	'.ht .detail{font-size:12px;overflow-wrap:anywhere}',
	'.ht .tsys{font-size:12.5px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}',
	'.ht .gap span{font-size:11.5px;color:var(--muted);padding:4px 0 12px 6px;font-style:italic}',
	'.ht .arctag{font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:var(--move);background:var(--move-bg);border-radius:3px;padding:1px 6px}',
	'.ht .arch{border:1px dashed var(--muted);border-radius:4px;padding:10px 12px;display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center;font-size:12.5px}',
	'.ht .arch .grow{flex:1 1 220px;min-width:0}',
	'.ht .arch code,.ht_files code{overflow-wrap:anywhere}',
	'.ht a.lnk,.ht_settings a.lnk{color:var(--p,#ac0000);font-weight:600;text-decoration:underline;cursor:pointer;white-space:nowrap}',
	'.dark .ht_settings a.lnk{color:#f85c22}',
	'.ht .empty{padding:30px 0;color:var(--muted)}',
	'.ht .button,.ht_files .button{margin:0}',
	'.ht_files{display:grid;gap:6px;margin:8px 0}',
	'.ht_files .file{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 10px;align-items:center;background:rgba(128,128,128,.12);border-radius:3px;padding:7px 10px;font-size:12.5px}',
	'.ht_files .file .meta{font-size:11.5px;opacity:.75}',
	'.ht_files .file .act{grid-column:2;grid-row:1 / span 2}',
	'.ht_files .on_page{font-size:10.5px;font-weight:700;text-transform:uppercase;color:#2f5f8a;background:#e4eef8;border-radius:3px;padding:1px 6px}',
	'.ht_settings .ht_actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center}',
	'.ht_settings .ht_status{font-size:12.5px;margin-top:6px}',
	'@media (max-width:485px){',
	'.page.history .scroll_content{padding:0 12px 30px}',
	'.ht .tday,.ht .gap{grid-template-columns:46px 18px minmax(0,1fr)}',
	'.ht .tdate .dn{font-size:20px}',
	'.ht .tdate .dw{letter-spacing:0;font-size:9.5px}',
	'.ht .tsteps .arr{display:none}',
	'.ht .tsteps .st{flex-basis:100%}',
	'.ht .chip.more{display:none}',
	'}'
].join('\n');

var HistoryHelpers = {

	style: function(){
		if(document.id('history_style')) return;
		new Element('style#history_style', {'type': 'text/css', 'text': HistoryStyle}).inject(document.head);
	},

	two: function(n){ return (n < 10 ? '0' : '') + n; },

	hm: function(t){
		var d = new Date(t * 1000);
		return HistoryHelpers.two(d.getHours()) + ':' + HistoryHelpers.two(d.getMinutes());
	},

	dayKey: function(t){
		var d = new Date(t * 1000);
		return d.getFullYear() + '-' + HistoryHelpers.two(d.getMonth() + 1) + '-' + HistoryHelpers.two(d.getDate());
	},

	dateText: function(iso, with_year){
		var p = iso.split('-'), d = new Date(+p[0], +p[1] - 1, +p[2]);
		return d.getDate() + ' ' + ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][d.getMonth()] + (with_year ? ' ' + d.getFullYear() : '');
	},

	size: function(bytes){
		return bytes < 1024 ? bytes + ' B' : Math.round(bytes / 1024) + ' KB';
	},

	quality: function(q){
		if(!q) return null;
		var found = window.Quality ? Quality.getQuality(q) : {};
		return (found && found.label) || q;
	},

	badge: function(type){
		var T = HistoryTypes[type] || {label: type, k: 'sys'};
		return new Element('span.badge', {
			'text': T.label,
			'style': 'color:var(--' + T.k + ');background:var(--' + T.k + '-bg)'
		});
	},

	fileRow: function(file, onChange){
		var act;
		if(file.on_page)
			act = new Element('span.on_page', {'text': 'On the page'});
		else
			act = new Element('a.button', {
				'text': 'Import',
				'events': {'click': function(){
					act.set('text', 'Importing…');
					Api.request('history.import', {'data': {'file': file.name}, 'onComplete': onChange});
				}}
			});

		return new Element('div.file').adopt(
			new Element('code.fn', {'text': file.name}),
			new Element('span.meta', {'text': HistoryHelpers.dateText(file.from) + ' – ' + HistoryHelpers.dateText(file.to, true) + ' · ' + file.events + ' events · ' + HistoryHelpers.size(file.size)}),
			new Element('span.act').grab(act)
		);
	},

	upload: function(onDone){
		var input = new Element('input', {'type': 'file', 'accept': '.jsonl,.json,.txt', 'styles': {'display': 'none'}}).inject(document.body);
		input.addEvent('change', function(){
			if(!input.files || !input.files[0]) return;
			var form = new FormData();
			form.append('file', input.files[0]);
			var xhr = new XMLHttpRequest();
			xhr.open('POST', Api.createUrl('history.import'));
			xhr.onload = function(){
				var json = {};
				try { json = JSON.parse(xhr.responseText); } catch(e){}
				input.destroy();
				onDone(json);
			};
			xhr.send(form);
		});
		input.click();
	}
};

Page.History = new Class({

	Extends: PageBase,

	order: 5,
	name: 'history',
	title: 'What happened to your movies',
	icon: 'list',

	filter: 'all',
	days: '90',

	indexAction: function(){
		var self = this;
		HistoryHelpers.style();

		if(!self.el_wrap){
			self.el_wrap = new Element('div.ht').adopt(
				new Element('div.ht_top').adopt(
					new Element('h2', {'text': 'History'}),
					self.chips = new Element('div.chips'),
					self.range = new Element('select.range', {'aria-label': 'Range', 'events': {'change': function(){
						self.days = self.range.get('value');
						self.loadEvents();
					}}}).adopt(
						new Element('option', {'value': '7', 'text': 'Last 7 days'}),
						new Element('option', {'value': '30', 'text': 'Last 30 days'}),
						new Element('option', {'value': '90', 'text': 'Last 90 days', 'selected': true}),
						new Element('option', {'value': '365', 'text': 'Last year'}),
						new Element('option', {'value': 'all', 'text': 'Everything'})
					)
				),
				self.list = new Element('div.tl')
			).inject(self.content);

			[['all', 'All'], ['snatched', 'Snatched'], ['downloaded', 'Downloaded'], ['failed', 'Failed'], ['library', 'Library'], ['app', 'App']].each(function(c, nr){
				new Element('a.chip' + (c[0] == self.filter ? '.on' : '') + (nr > 2 ? '.more' : ''), {
					'text': c[1],
					'data-filter': c[0],
					'events': {'click': function(){
						self.filter = c[0];
						self.chips.getElements('.chip').removeClass('on');
						this.addClass('on');
						self.loadEvents();
					}}
				}).inject(self.chips);
			});

			App.on('history.add', function(){
				if(self.el.hasClass('active')) self.loadEvents();
			});
		}

		self.loadEvents();
	},

	loadEvents: function(){
		var self = this;
		if(self.request && self.request.running) self.request.cancel();
		self.request = Api.request('history.list', {
			'data': {'filter': self.filter, 'days': self.days},
			'onComplete': self.render.bind(self)
		});
	},

	render: function(json){
		var self = this;
		self.list.empty();
		if(!json || !json.success){
			self.list.grab(new Element('div.empty', {'text': 'Could not load the history.'}));
			return;
		}

		var days = [], idx = {};
		json.events.each(function(e){
			var k = HistoryHelpers.dayKey(e.time);
			if(!(k in idx)){ idx[k] = days.length; days.push({'t': e.time, 'ev': []}); }
			days[idx[k]].ev.push(e);
		});

		if(!days.length)
			self.list.grab(new Element('div.empty', {'text': self.filter == 'all' ? 'Nothing has happened yet. Snatches, downloads and updates will show up here.' : 'Nothing of this kind in this range.'}));

		var prev = null;
		days.each(function(d){
			if(prev){
				var a = new Date(prev * 1000), b = new Date(d.t * 1000);
				a.setHours(0, 0, 0, 0); b.setHours(0, 0, 0, 0);
				var quiet = Math.round((a - b) / 86400000) - 1;
				if(quiet >= 1) self.list.grab(self.gap(quiet + (self.archivedBetween(json.files, d.t, prev) ? ' day' + (quiet > 1 ? 's' : '') + ' in archive files, not on this page' : ' quiet day' + (quiet > 1 ? 's' : ''))));
			}
			prev = d.t;
			self.list.grab(self.day(d));
		});

		// Only where the page really reaches the start: the oldest day shown is the day history began
		var began = json.began || (json.first_time && HistoryHelpers.dayKey(json.first_time));
		if(began && days.length && HistoryHelpers.dayKey(days[days.length - 1].t) == began)
			self.list.grab(self.gap('History began here, ' + HistoryHelpers.dateText(began, true)));

		self.list.grab(self.archiveStop(json));
	},

	// Is part of the gap between two shown days held in an archive file that is not on the page?
	archivedBetween: function(files, older, newer){
		var from = HistoryHelpers.dayKey(older), to = HistoryHelpers.dayKey(newer);
		return (files || []).some(function(f){
			return !f.on_page && f.first && f.first < to && f.last > from;
		});
	},

	gap: function(text){
		return new Element('div.gap').adopt(new Element('div'), new Element('div.rail'), new Element('span', {'text': text}));
	},

	day: function(d){
		var by_movie = {}, order = [], sys = [];
		d.ev.slice().sort(function(a, b){ return a.time - b.time; }).each(function(e){
			var key = e.media_id || e.title;
			if(!key){ sys.push(e); return; }
			key = key + '|' + (e.archive || '');
			if(!by_movie[key]){ by_movie[key] = []; order.push(key); }
			by_movie[key].push(e);
		});

		var any_fail = d.ev.some(function(e){ return HistoryTypes[e.type] && HistoryTypes[e.type].k == 'fail'; }),
			date = new Date(d.t * 1000),
			body = new Element('div.tbody');

		order.each(function(key){
			var evs = by_movie[key], first = evs[0], last = evs[evs.length - 1],
				q = HistoryHelpers.quality((evs.filter(function(e){ return e.quality; })[0] || {}).quality),
				failed = evs.some(function(e){ return e.type == 'failed'; }),
				steps = new Element('div.tsteps');

			evs.each(function(e, nr){
				if(nr) steps.grab(new Element('span.arr', {'text': '→'}));
				steps.grab(new Element('span.st').adopt(
					HistoryHelpers.badge(e.type),
					new Element('span.tnum.muted', {'text': HistoryHelpers.hm(e.time)}),
					e.source ? new Element('span.muted', {'text': '· ' + e.source}) : null
				));
			});

			body.grab(new Element('div.tcard' + (failed ? '.failed' : '')).adopt(
				new Element('div.chead').adopt(
					new Element('span.title', {'text': first.title || 'Unknown movie'}),
					first.year ? new Element('span.muted', {'text': '(' + first.year + ')'}) : null,
					q ? new Element('span.q', {'text': q}) : null,
					first.archive ? new Element('span.arctag', {'text': 'Archive', 'title': first.archive}) : null
				),
				steps,
				last.detail ? new Element('div.detail.muted', {'text': last.detail}) : null
			));
		});

		sys.each(function(e){
			body.grab(new Element('div.tsys').adopt(
				HistoryHelpers.badge(e.type),
				new Element('span.tnum.muted', {'text': HistoryHelpers.hm(e.time)}),
				new Element('span', {'text': e.detail || ''}),
				e.archive ? new Element('span.arctag', {'text': 'Archive', 'title': e.archive}) : null
			));
		});

		return new Element('div.tday').adopt(
			new Element('div.tdate').adopt(
				new Element('div.dw', {'text': ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][date.getDay()]}),
				new Element('div.dn.tnum', {'text': date.getDate()}),
				new Element('div.dm', {'text': ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][date.getMonth()]})
			),
			new Element('div.rail').grab(new Element('span.dot' + (any_fail ? '.fail' : (!order.length ? '.sys' : '')))),
			body
		);
	},

	archiveStop: function(json){
		var self = this,
			box = new Element('div.tbody'),
			keep_text = 'Keeping ' + (HistoryKeep[json.keep] || json.keep) + '.',
			settings_link = new Element('a.lnk', {'text': 'Change in Settings ›', 'href': App.createUrl('settings/general') + '#history'}),
			reload = function(){ self.loadEvents(); };

		Object.each(json.imported || {}, function(count, name){
			box.grab(new Element('div.arch').adopt(
				new Element('span', {'text': '↺'}),
				new Element('span.grow').adopt(
					new Element('b', {'text': 'Imported from archive: '}),
					new Element('code', {'text': name}),
					new Element('span', {'text': ', ' + count + ' events'})
				),
				new Element('a.button', {'text': 'Remove from page', 'events': {'click': function(){
					Api.request('history.unimport', {'data': {'file': name}, 'onComplete': reload});
				}}})
			));
		});

		var waiting = (json.files || []).filter(function(f){ return !f.on_page && !(json.imported || {})[f.name]; }),
			newest = waiting[0];

		if(newest){
			box.grab(new Element('div.arch').adopt(
				new Element('span', {'text': '🗄'}),
				new Element('span.grow').adopt(
					new Element('b', {'text': 'Older history is archived. '}),
					new Element('span', {'text': HistoryHelpers.dateText(newest.from) + ' – ' + HistoryHelpers.dateText(newest.to, true) + ' · '}),
					new Element('code', {'text': newest.name}),
					waiting.length > 1 ? new Element('span.muted', {'text': ' (and ' + (waiting.length - 1) + ' older, in Settings)'}) : null,
					new Element('br'),
					new Element('span.muted', {'text': keep_text + ' '}),
					settings_link
				),
				new Element('a.button', {'text': 'Import', 'events': {'click': function(){
					this.set('text', 'Importing…');
					Api.request('history.import', {'data': {'file': newest.name}, 'onComplete': reload});
				}}})
			));
		}
		else {
			box.grab(new Element('div.arch').adopt(
				new Element('span', {'text': '🗄'}),
				new Element('span.grow').adopt(
					new Element('b', {'text': (json.files || []).length ? 'Every archive file is on the page. ' : 'No archive files yet. '}),
					new Element('span.muted', {'text': keep_text + ' '}),
					settings_link
				),
				new Element('a.button', {'text': 'Import a file…', 'events': {'click': function(){
					HistoryHelpers.upload(reload);
				}}})
			));
		}

		return new Element('div.tday').adopt(
			new Element('div.tdate').grab(new Element('div.dw', {'text': 'Archive'})),
			new Element('div.rail').grab(new Element('span.dot.sys', {'styles': {'border-style': 'dashed'}})),
			box
		);
	}
});

// Settings → General → History: a link to the page, the archive files, Import and Archive now
var HistorySettings = new Class({

	initialize: function(){
		App.addEvent('loadSettings', this.addToSettings.bind(this));
	},

	addToSettings: function(){
		var self = this,
			setting_page = App.getPage('Settings');

		setting_page.addEvent('create', function(){
			var fieldset = setting_page.tabs.general.groups.history;
			if(!fieldset) return;
			HistoryHelpers.style();
			fieldset.addClass('ht_settings');

			var keep_hint = fieldset.getElement('select[name=history[keep]]');
			keep_hint = keep_hint && keep_hint.getParent('.ctrlHolder');
			if(keep_hint)
				new Element('a.lnk', {'text': 'Open History ›', 'href': App.createUrl('history'), 'styles': {'margin-left': 6}})
					.inject(keep_hint.getElement('.formHint') || keep_hint);

			self.files = new Element('div.ht_files');
			self.status = new Element('div.ht_status');

			new Element('div.ctrlHolder').adopt(
				new Element('label', {'text': 'Archive files'}),
				new Element('div', {'styles': {'flex': 1, 'min-width': 0}}).adopt(
					new Element('div.formHint', {'html': 'Import puts a file back on the History page. The file is not changed. '}).grab(
						new Element('a.lnk', {'text': 'Open History ›', 'href': App.createUrl('history')})
					),
					self.files,
					new Element('div.ht_actions').adopt(
						new Element('a.button', {'text': 'Import a file from elsewhere…', 'events': {'click': function(){
							HistoryHelpers.upload(self.done.bind(self));
						}}}),
						new Element('a.button', {'text': 'Archive now', 'events': {'click': function(){
							self.status.set('text', 'Archiving…');
							Api.request('history.archive', {'onComplete': self.done.bind(self)});
						}}})
					),
					self.status
				)
			).inject(fieldset);

			self.loadFiles();
		});
	},

	done: function(json){
		var self = this;
		if(!json || json.success === false)
			self.status.set('text', (json && json.error) || 'That did not work, see the log.');
		else if(json.message)
			self.status.set('text', json.message);
		else if(json.archived !== undefined)
			self.status.set('text', json.archived ? 'Archived ' + json.archived + ' events.' : 'Nothing is older than the limit yet.');
		else if(json.added !== undefined)
			self.status.set('text', 'Imported ' + json.added + ' events from ' + json.name + (json.skipped ? ' (' + json.skipped + ' were already there)' : '') + '.');
		self.loadFiles();
	},

	loadFiles: function(){
		var self = this;
		Api.request('history.files', {'onComplete': function(json){
			self.files.empty();
			if(!json || !json.files || !json.files.length){
				self.files.grab(new Element('div.formHint', {'text': 'None yet, in ' + ((json && json.folder) || 'the archive folder') + '.'}));
				return;
			}
			json.files.each(function(f){
				self.files.grab(HistoryHelpers.fileRow(f, self.done.bind(self)));
			});
		}});
	}
});

new HistorySettings();
