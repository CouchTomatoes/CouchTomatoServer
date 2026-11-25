// Movie details: three views on one page, switched top right and saved in Settings -> Screens.
//   Poster  : poster and facts on the left, where the movie is (Wanted -> Snatched -> Download -> In library) on the right.
//   Hero    : a wide banner on top (poster, title, facts), the releases below.
//   Classic : the old CouchPotato overlay, exactly as it was. None of the new parts show there.
// The backdrop (Full / Small / None) applies to Poster and Hero only.
// Plugins still add their parts with addSection() / addButton(); every view shows the same sections.
// Styles live here (injected once) because the Sass build is not part of tools/jsbuild.

var MovieDetailsStyle = [
	'.mdx-wrap{--acc:#ac0000;--ok:#1d7a3a;--ok-bg:#e3f5e8;--off:#ebebeb;--line:#e2e2e2;--muted:#6a6a6a;--bg:#fff;--text:#000;--track:#3a3a3a}',
	'.dark .mdx-wrap,.mdx-wrap.dark{--acc:#f85c22;--ok:#6ad68b;--ok-bg:#20402a;--off:#363636;--line:#404040;--muted:#a8a8a8;--bg:#2d2d2d;--text:#fff}',

	// Which parts show in which view
	'.mdx-wrap .mdx,.mdx-wrap .mdx-bg{display:none}',
	'.mdx-wrap.mdx-v-poster .mdx,.mdx-wrap.mdx-v-hero .mdx{display:block}',
	'.mdx-wrap.mdx-v-poster .scroll_content > .head,.mdx-wrap.mdx-v-hero .scroll_content > .head{display:none}',
	'.mdx-wrap.mdx-v-poster .section_description,.mdx-wrap.mdx-v-hero .section_description,',
	'.mdx-wrap.mdx-v-poster .section_trailer,.mdx-wrap.mdx-v-hero .section_trailer{display:none}',

	// The view / backdrop switch, top right
	'.mdx-switch{display:flex;justify-content:flex-end;flex-wrap:wrap;gap:8px;padding:12px 20px 0;position:relative;z-index:3}',
	'.mdx-v-classic .mdx-switch{padding:10px 20px 0}',
	'.mdx-seg{display:inline-flex;border:1px solid var(--line);border-radius:4px;overflow:hidden;background:var(--bg)}',
	'.mdx-seg button{border:0;background:transparent;color:var(--muted);font:inherit;font-size:12px;padding:5px 10px;cursor:pointer;white-space:nowrap}',
	'.mdx-seg button.on{background:var(--acc);color:#fff}',
	'.mdx-v-classic .mdx-seg.mdx-bd-seg{display:none}',

	// Backdrop layer. Full: stays behind the whole page while it scrolls. Small: a band on top.
	'.mdx-wrap:not(.mdx-v-classic).mdx-bd-full.mdx-has-bd .mdx-bg{display:block;position:sticky;top:0;height:100vh;margin-bottom:-100vh;z-index:0;',
	'background:linear-gradient(rgba(12,12,12,.78),rgba(12,12,12,.9)),var(--mdx-bd) center 25%/cover no-repeat}',
	'.mdx-wrap:not(.mdx-v-classic).mdx-bd-full.mdx-has-bd .scroll_content{background:#161616}',
	'.mdx-wrap:not(.mdx-v-classic).mdx-bd-full.mdx-has-bd .mdx-switch .mdx-seg{background:rgba(0,0,0,.45);border-color:rgba(255,255,255,.3)}',
	'.mdx-wrap:not(.mdx-v-classic).mdx-bd-full.mdx-has-bd .mdx-switch .mdx-seg button:not(.on){color:#ddd}',
	'.mdx-wrap .scroll_content > *{position:relative;z-index:1}',
	'.mdx-wrap .scroll_content > .mdx-bg{position:sticky;z-index:0}',
	'.mdx-wrap .scroll_content > .mdx-switch{z-index:3}',
	'.mdx-wrap .scroll_content > .head{z-index:2}',
	'.mdx-band{display:none;pointer-events:none}',
	'.mdx-bd-small.mdx-has-bd .mdx-band{display:block;position:absolute;left:0;right:0;top:-50px;',
	'background:linear-gradient(90deg,rgba(0,0,0,.85),rgba(0,0,0,.25)),var(--mdx-bd) center 30%/cover no-repeat,#1a1a2e}',
	'.mdx-v-hero.mdx-bd-small.mdx-has-bd .mdx-band{bottom:0}',
	'.mdx-v-poster.mdx-bd-small.mdx-has-bd .mdx-band{height:140px}',
	'.mdx-v-poster.mdx-bd-small.mdx-has-bd .mdx-top{padding-top:110px}',

	// Layout
	'.mdx{position:relative;color:var(--text)}',
	'.mdx-top{position:relative;display:flex;gap:22px;padding:18px 20px 20px}',
	'.mdx-side{width:200px;flex:none}',
	'.mdx-poster{position:relative;width:200px;height:300px;border-radius:4px;background:var(--off) center/cover no-repeat;box-shadow:0 6px 20px rgba(0,0,0,.35)}',
	'.mdx-play{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:54px;height:54px;border-radius:50%;background:rgba(0,0,0,.6);',
	'border:2px solid #fff;color:#fff;font-size:20px;display:flex;align-items:center;justify-content:center;cursor:pointer;padding-left:4px;box-sizing:border-box}',
	'.mdx-no-trailer .mdx-play{display:none}',
	'.mdx-facts{margin-top:12px;font-size:13px}',
	'.mdx-facts div{display:flex;justify-content:space-between;gap:8px;border-bottom:1px solid var(--line);padding:3px 0}',
	'.mdx-facts span:first-child{color:var(--muted)}',
	'.mdx-facts span:last-child{text-align:right}',
	'.mdx-main{flex:1;min-width:0}',
	'.mdx-title{font-size:30px;font-weight:300;line-height:1.2;margin:0}',
	'.mdx-title .mdx-year{opacity:.7}',
	'.mdx-meta{font-size:13px;opacity:.85;margin-top:2px}',
	'.mdx-plot{font-size:13px;line-height:1.5;max-width:680px;margin:8px 0 12px;opacity:.9}',
	'.mdx-row{display:flex;align-items:center;flex-wrap:wrap;gap:8px}',
	'.mdx-stepsrow{margin:10px 0}',
	'.mdx-badge{display:inline-block;font-size:11px;font-weight:700;border-radius:3px;padding:1px 7px;white-space:nowrap;background:var(--off);color:var(--muted)}',
	'.mdx-actions{margin:14px 0 6px}',
	'.mdx-slot .section{padding-left:0;padding-right:0}',

	// Steps: the same pill everywhere. Done = green with a tick, now = accent, later = grey.
	'.mdx-steps{display:inline-flex;align-items:center;flex-wrap:wrap;row-gap:5px;font-size:12px}',
	'.mdx-steps span{padding:3px 9px;border-radius:12px;background:var(--off);color:var(--muted);white-space:nowrap}',
	'.mdx-steps span.done{background:var(--ok-bg);color:var(--ok)}',
	'.mdx-steps span.now{background:var(--acc);color:#fff}',
	'.mdx-steps em{width:14px;height:2px;background:var(--line)}',
	'.mdx-steps em.lit{background:var(--ok)}',
	'.mdx-v-hero .mdx-steps{font-size:11px;font-weight:700}',
	'.mdx-v-hero .mdx-steps span{padding:1px 8px;border-radius:9px}',
	'.mdx-v-hero .mdx-steps em{width:10px}',

	// Buttons and their menus (Quality / Category / more)
	'.mdx-btn{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--acc);color:var(--acc);background:transparent;border-radius:3px;',
	'padding:6px 12px;font:inherit;font-size:13px;line-height:1.3;cursor:pointer;white-space:nowrap;text-decoration:none}',
	'.mdx-btn.solid{background:var(--acc);color:#fff}',
	'.mdx-btn.quiet{border-color:var(--line);color:var(--text)}',
	'.mdx-btn[disabled]{opacity:.5;cursor:default}',
	'.mdx-btn .car{font-size:10px;opacity:.8}',
	'.mdx-mwrap{position:relative;display:inline-block}',
	'.mdx-menu{display:none;position:absolute;left:0;top:calc(100% + 4px);min-width:190px;max-height:320px;overflow-y:auto;background:var(--bg);color:var(--text);',
	'border:1px solid var(--line);border-radius:4px;box-shadow:0 10px 30px rgba(0,0,0,.35);z-index:6;padding:4px 0;text-align:left}',
	'.mdx-mwrap.open .mdx-menu{display:block}',
	'.mdx-menu.right{left:auto;right:0}',
	'.mdx-menu a{display:block;padding:8px 14px;font-size:13px;color:inherit;text-decoration:none;cursor:pointer;white-space:nowrap}',
	'.mdx-menu a:hover{background:var(--off)}',
	'.mdx-menu a.cur{font-weight:600}',
	'.mdx-menu a.bad{color:#c4002f}',
	'.dark .mdx-menu a.bad,.mdx-wrap.dark .mdx-menu a.bad{color:#ff7b8a}',
	'.mdx-menu .ck{display:inline-block;width:18px;color:var(--acc);font-weight:700}',
	'.mdx-menu .sub{padding-left:32px;font-size:12px}',
	'.mdx-menu hr{border:0;border-top:1px solid var(--line);margin:4px 0}',

	// White text on a backdrop (Small band, Hero only; Full is the dark theme already)
	'.mdx-v-hero.mdx-bd-small.mdx-has-bd .mdx-top{color:#fff;min-height:230px;align-items:flex-end;box-sizing:border-box}',
	'.mdx-v-hero.mdx-bd-small.mdx-has-bd .mdx-top .mdx-btn:not(.solid){color:#fff;border-color:rgba(255,255,255,.55)}',
	'.mdx-v-hero .mdx-side{width:130px}',
	'.mdx-v-hero .mdx-poster{width:130px;height:195px}',
	'.mdx-v-hero .mdx-play{width:38px;height:38px;font-size:14px}',
	'.mdx-v-hero .mdx-facts{display:none}',
	'.mdx-v-hero.mdx-bd-none .mdx-top,.mdx-v-hero:not(.mdx-has-bd) .mdx-top{border-bottom:1px solid var(--line)}',

	// Trailer pop-up and the "saved" message
	'.mdx-video{position:fixed;inset:0;background:rgba(0,0,0,.78);display:flex;align-items:center;justify-content:center;padding:14px;z-index:1000;pointer-events:auto}',
	'.mdx-vbox{width:880px;max-width:100%;background:#000;border-radius:6px;overflow:hidden;box-shadow:0 16px 50px rgba(0,0,0,.6);color:#fff}',
	'.mdx-vh{display:flex;align-items:center;gap:10px;padding:10px 14px;background:#111;font-size:14px}',
	'.mdx-vh button{margin-left:auto;background:none;border:1px solid #666;color:#fff;border-radius:3px;padding:3px 10px;cursor:pointer;font:inherit}',
	'.mdx-vbox iframe{display:block;width:100%;aspect-ratio:16/9;height:auto;border:0;background:#000}',
	'.mdx-toast{position:fixed;right:20px;bottom:20px;background:#222;color:#fff;padding:9px 14px;border-radius:4px;font-size:13px;',
	'box-shadow:0 6px 20px rgba(0,0,0,.4);z-index:1001;opacity:0;transition:opacity .25s;pointer-events:none}',
	'.mdx-toast.on{opacity:1}',

	// Phone
	'@media (max-width:485px){',
	'.mdx-switch{padding:8px 10px 0;justify-content:flex-start}',
	'.mdx-top{padding:12px 10px 14px;gap:12px}',
	'.mdx-v-poster .mdx-top{flex-direction:column}',
	'.mdx-v-poster .mdx-side{width:100%;display:flex;gap:12px}',
	'.mdx-v-poster .mdx-poster{width:100px;height:150px;flex:none}',
	'.mdx-v-poster .mdx-facts{margin-top:0;flex:1}',
	'.mdx-v-hero .mdx-side,.mdx-v-hero .mdx-poster{width:80px}',
	'.mdx-v-hero .mdx-poster{height:120px}',
	'.mdx-v-hero.mdx-bd-small.mdx-has-bd .mdx-top{min-height:170px}',
	'.mdx-v-hero .mdx-plot{display:none}',
	'.mdx-title{font-size:22px}',
	'.mdx-v-hero .mdx-steps{flex:1 1 100%}',
	'}'
].join('');


var MovieDetails = new Class({

	Extends: BlockBase,

	sections: null,
	buttons: null,

	views: [['hero', '▭ Hero'], ['poster', '▯ Poster'], ['classic', '⟲ Classic']],
	backdrops: [['full', '⛶ Full'], ['small', '▭ Small'], ['none', '☐ None']],
	step_names: ['Wanted', 'Snatched', 'Download', 'In library'],

	initialize: function(parent, options){
		var self = this;

		self.sections = {};
		self.movie = parent;
		self.options = options || {};

		MovieDetails.injectStyle();

		var screens = App.getOption('screens') || {};
		self.view = screens.details_view || 'poster';
		self.backdrop = screens.details_backdrop || 'full';

		self.wrap = new Element('div.mdx-wrap').grab(
			self.el = new Element('div', {
				'class': 'page active movie_details level_' + (self.options.level || 0)
			}).adopt(
				self.overlay = new Element('div.overlay', {
					'events': {
						'click': self.close.bind(self)
					}
				}).grab(
					new Element('a.close.icon-left-arrow')
				),
				self.content = new Element('div.scroll_content').adopt(
					self.bg = new Element('div.mdx-bg'),
					self.createSwitch(),
					new Element('div.head').adopt(
						new Element('h1').grab(
							self.title_dropdown = new BlockMenu(self, {
								'class': 'title',
								'button_text': self.titleWithYear(parent.getTitle()),
								'button_class': 'icon-dropdown'
							})
						),
						self.buttons = new Element('div.buttons')
					),
					self.createModern(),
					self.sections_el = new Element('div.mdx-sections')
				)
			)
		);

		var eta_date = parent.getETA('%b %Y') ;
		self.addSection('description', new Element('div').adopt(
			new Element('div', {
				'text': parent.get('plot')
			}),
			new Element('div.meta', {
				'html':
					(eta_date ? ('<span>ETA:' + eta_date + '</span>') : '') +
					'<span>' + (parent.get('genres') || []).join(', ') + '</span>'
			})
		));


		// Title dropdown (Classic)
		var titles = parent.get('info').titles || [];
		$(self.title_dropdown).addEvents({
			'click:relay(li a)': function(e, el){
				(e).stopPropagation();
				self.setTitle(el.get('text'));
			}
		});

		titles.each(function(t){
			self.title_dropdown.addLink(new Element('a', {
				'text': t,
				'class': parent.get('title') == t ? 'icon-ok' : ''
			}));
		});

		if(self.backdrop_url){
			self.wrap.addClass('mdx-has-bd');
			self.wrap.style.setProperty('--mdx-bd', 'url("' + self.backdrop_url.replace(/"/g, '%22') + '")');
		}

		// A click anywhere else closes an open menu
		self.wrap.addEvent('click', function(e){
			if(!e.target.getParent('.mdx-mwrap'))
				self.closeMenus();
		});

		self.applyView();
	},

	toElement: function(){
		return this.wrap;
	},

	titleWithYear: function(title){
		var year = this.movie.get('year');
		return title + (year ? ' (' + year + ')' : '');
	},

	setTitle: function(title){
		var self = this;

		Api.request('movie.edit', {
			'data': {
				'id': self.movie.get('_id'),
				'default_title': title
			}
		});

		$(self.title_dropdown).getElements('.icon-ok').removeClass('icon-ok');
		$(self.title_dropdown).getElements('li a').each(function(a){
			if(a.get('text') == title) a.addClass('icon-ok');
		});
		self.title_dropdown.button.set('text', self.titleWithYear(title));

		self.current_title = title;
		self.title_name.set('text', title);
		self.fillMoreMenu();
		self.toast('Title changed to ' + title);
	},

	// ----- The view switch -----

	createSwitch: function(){
		var self = this;

		var seg = function(list, key, cls){
			var el = new Element('div.mdx-seg' + (cls ? '.' + cls : ''));
			list.each(function(o){
				new Element('button', {
					'type': 'button',
					'text': o[1],
					'data-v': o[0],
					'events': {
						'click': function(e){
							(e).stop();
							self.pick(key, o[0]);
						}
					}
				}).inject(el);
			});
			return el;
		};

		return new Element('div.mdx-switch').adopt(
			self.view_seg = seg(self.views, 'view'),
			self.bd_seg = seg(self.backdrops, 'backdrop', 'mdx-bd-seg')
		);
	},

	pick: function(key, value){
		var self = this;
		if(self[key] == value) return;

		self[key] = value;
		self.applyView();

		// Same setting as Settings -> Screens, so the choice sticks on every browser
		var name = key == 'view' ? 'details_view' : 'details_backdrop';
		var screens = App.getOption('screens');
		if(screens) screens[name] = value;

		Api.request('settings.save', {
			'data': {
				'section': 'screens',
				'name': name,
				'value': value
			}
		});
	},

	applyView: function(){
		var self = this;

		var cls = self.wrap.get('class').split(' ').filter(function(c){
			return c.indexOf('mdx-v-') !== 0 && c.indexOf('mdx-bd-') !== 0 && c != 'dark';
		});
		cls.push('mdx-v-' + self.view, 'mdx-bd-' + self.backdrop);

		// Full backdrop: the whole page is dark, whatever the app's theme
		if(self.view != 'classic' && self.backdrop == 'full' && self.backdrop_url)
			cls.push('dark');

		self.wrap.set('class', cls.join(' '));

		[[self.view_seg, self.view], [self.bd_seg, self.backdrop]].each(function(s){
			s[0].getElements('button').each(function(b){
				b[b.get('data-v') == s[1] ? 'addClass' : 'removeClass']('on');
			});
		});

		// Poster keeps the releases beside the poster, Hero and Classic under the top part
		if(self.view == 'poster')
			self.slot.grab(self.sections_el);
		else
			self.sections_el.inject(self.content);

		self.closeMenus();
	},

	// ----- Poster / Hero top part -----

	createModern: function(){
		var self = this,
			m = self.movie,
			info = m.data.info || {};

		var images = info.images || {};
		self.backdrop_url = (images.backdrop_original || [])[0] || (images.backdrop || [])[0] || null;

		var poster = null;
		if(m.data.files && m.data.files.image_poster && m.data.files.image_poster.length)
			poster = Api.createUrl('file.cache') + m.data.files.image_poster[0].split(Api.getOption('path_sep')).pop();
		else if(images.poster && images.poster.length)
			poster = images.poster[0];

		self.current_title = m.getTitle();

		self.mdx = new Element('div.mdx').adopt(
			new Element('div.mdx-band'),
			new Element('div.mdx-top').adopt(
				new Element('div.mdx-side').adopt(
					new Element('div.mdx-poster', {
						'styles': poster ? {'background-image': 'url("' + poster + '")'} : {}
					}).grab(
						new Element('span.mdx-play', {
							'text': '▶',
							'title': 'Play the trailer',
							'events': {'click': self.playTrailer.bind(self)}
						})
					),
					self.createFacts()
				),
				new Element('div.mdx-main').adopt(
					new Element('h1.mdx-title').adopt(
						self.title_name = new Element('span', {'text': self.current_title}),
						m.get('year') ? new Element('span.mdx-year', {'text': ' ' + m.get('year')}) : null
					),
					new Element('div.mdx-meta', {'text': self.metaLine()}),
					new Element('div.mdx-row.mdx-stepsrow').adopt(
						self.createSteps(),
						self.quality_badge = new Element('span.mdx-badge', {'text': (m.profile && m.profile.get) ? m.profile.get('label') : ''})
					),
					info.plot ? new Element('div.mdx-plot', {'text': info.plot}) : null,
					self.actions_el = new Element('div.mdx-row.mdx-actions'),
					self.slot = new Element('div.mdx-slot')
				)
			)
		);

		if(!self.quality_badge.get('text')) self.quality_badge.hide();

		self.createActions();

		return self.mdx;
	},

	findAction: function(klass){
		var found = null;
		(this.movie.actions || []).each(function(a){
			if(!found && instanceOf(a, klass)) found = a;
		});
		return found;
	},

	runtime: function(){
		var r = parseInt((this.movie.data.info || {}).runtime, 10);
		if(!r) return null;
		return Math.floor(r / 60) + 'h ' + (r % 60) + 'm';
	},

	imdbRating: function(){
		var rating = ((this.movie.data.info || {}).rating || {}).imdb;
		if(typeOf(rating) == 'array') rating = rating[0];
		rating = parseFloat(rating);
		return rating ? rating.toFixed(1) : null;
	},

	metaLine: function(){
		var info = this.movie.data.info || {},
			parts = [];
		if(this.runtime()) parts.push(this.runtime());
		if(info.directors && info.directors.length) parts.push(info.directors.slice(0, 2).join(', '));
		if(info.genres && info.genres.length) parts.push(info.genres.slice(0, 3).join(', '));
		if(this.imdbRating()) parts.push('IMDb ' + this.imdbRating());
		return parts.join(' · ');
	},

	createFacts: function(){
		var self = this,
			m = self.movie,
			info = m.data.info || {},
			category = m.data.category_id ? CategoryList.getCategory(m.data.category_id) : null;

		var facts = [
			['Year', info.year],
			['Runtime', self.runtime()],
			['Director', (info.directors || []).slice(0, 2).join(', ')],
			['Quality', m.profile && m.profile.get ? m.profile.get('label') : null],
			['Category', category ? category.get('label') : 'None'],
			['Released', info.released && info.released != 'None' ? info.released : null],
			['IMDb', self.imdbRating()]
		];

		var el = new Element('div.mdx-facts');
		facts.each(function(f){
			if(!f[1]) return;
			var row = new Element('div').adopt(
				new Element('span', {'text': f[0]}),
				new Element('span', {'text': f[1]})
			).inject(el);
			if(f[0] == 'Quality') self.quality_fact = row.getLast();
			if(f[0] == 'Category') self.category_fact = row.getLast();
		});
		return el;
	},

	// Where the movie is now. 0 Wanted, 1 Snatched, 2 Download, 3 In library, 4 all done.
	// Only what the database knows: no download % here yet (that comes with the live status).
	stage: function(){
		var m = this.movie,
			releases = m.data.releases || [];
		var has = function(status){
			return releases.some(function(r){ return r.status == status; });
		};

		if(m.data.status == 'done' || has('done') || has('seeding')) return 4;
		if(has('downloaded')) return 3;
		if(has('snatched')) return 2;
		return 0;
	},

	createSteps: function(){
		var self = this,
			stage = self.stage(),
			el = new Element('span.mdx-steps');

		self.step_names.each(function(name, i){
			if(i > 0) new Element('em', {'class': i <= stage ? 'lit' : ''}).inject(el);
			var state = i < stage ? 'done' : (i == stage ? 'now' : '');
			var label = name;
			if(state == 'done') label = '✓ ' + (name == 'Download' ? 'Downloaded' : name);
			else if(state == 'now' && name == 'Download') label = 'Downloading';
			new Element('span', {'class': state, 'text': label}).inject(el);
		});

		return el;
	},

	// ----- Buttons -----

	createActions: function(){
		var self = this,
			m = self.movie;

		if(self.findAction(MA.Refresh))
			new Element('button.mdx-btn.solid', {
				'type': 'button',
				'text': '⟳ Search now',
				'title': 'Refresh the movie info and search all your providers again',
				'events': {
					'click': function(e){
						(e).stop();
						Api.request('media.refresh', {'data': {'id': m.get('_id')}});
						self.toast('Searching for ' + self.current_title + '…');
					}
				}
			}).inject(self.actions_el);

		self.trailer_btn = new Element('button.mdx-btn', {
			'type': 'button',
			'text': '▶ Trailer',
			'events': {'click': self.playTrailer.bind(self)}
		}).inject(self.actions_el);

		if(self.findAction(MA.Profile)){
			var profiles = Quality.getActiveProfiles();
			if(profiles.length > 0)
				self.quality_picker = self.createPicker('Quality', profiles.map(function(p){
					return {'text': p.get('label'), 'value': p.get('_id')};
				}), m.profile && m.profile.get ? m.profile.get('_id') : null, function(item){
					Api.request('movie.edit', {'data': {'id': m.get('_id'), 'profile_id': item.value}});
					self.quality_badge.set('text', item.text).show();
					if(self.quality_fact) self.quality_fact.set('text', item.text);
					self.toast('Quality changed to ' + item.text + ' · saved');
				}).inject(self.actions_el);
		}

		if(self.findAction(MA.Category)){
			var categories = CategoryList.getAll();
			if(categories.length > 0){
				var items = [{'text': 'None', 'value': ''}].concat(categories.map(function(c){
					return {'text': c.get('label'), 'value': c.get('_id')};
				}));
				self.createPicker('Category', items, m.data.category_id || '', function(item){
					Api.request('movie.edit', {'data': {'id': m.get('_id'), 'category_id': item.value}});
					if(self.category_fact) self.category_fact.set('text', item.text);
					self.toast('Category changed to ' + item.text + ' · saved');
				}).inject(self.actions_el);
			}
		}

		// Rare actions
		self.more = new Element('div.mdx-mwrap').adopt(
			new Element('button.mdx-btn.quiet', {
				'type': 'button',
				'text': '⋯',
				'title': 'More actions',
				'aria-label': 'More actions',
				'events': {
					'click': function(e){
						(e).stop();
						self.toggleMenu(self.more);
					}
				}
			}),
			self.more_menu = new Element('div.mdx-menu.right')
		).inject(self.actions_el);

		self.fillMoreMenu();
	},

	fillMoreMenu: function(){
		var self = this,
			m = self.movie,
			menu = self.more_menu;

		menu.empty();

		var link = function(text, fn, cls){
			return new Element('a', {
				'text': text,
				'class': cls || '',
				'events': {
					'click': function(e){
						(e).stop();
						self.closeMenus();
						fn();
					}
				}
			}).inject(menu);
		};

		var titles = ((m.data.info || {}).titles || []).filter(function(t, i, all){ return all.indexOf(t) == i; });
		if(titles.length > 1){
			new Element('a', {'text': 'Change title to:', 'styles': {'cursor': 'default', 'opacity': .7}}).inject(menu);
			titles.each(function(t){
				var a = link('', function(){ self.setTitle(t); }, 'sub' + (t == self.current_title ? ' cur' : ''));
				a.adopt(new Element('span.ck', {'text': t == self.current_title ? '✓' : ''}), document.createTextNode(t));
			});
			new Element('hr').inject(menu);
		}

		var imdb = m.getIdentifier ? m.getIdentifier() : null;
		if(imdb)
			new Element('a', {
				'text': 'IMDb ↗',
				'href': 'http://www.imdb.com/title/' + imdb + '/',
				'target': '_blank',
				'events': {'click': function(){ self.closeMenus(); }}
			}).inject(menu);

		var readd = self.findAction(MA.Readd);
		if(readd && readd.el)
			link('Add again (ignore the old downloads)', function(){
				readd.doReadd({'stopPropagation': function(){}});
				self.toast('Added ' + self.current_title + ' again');
			});

		var del = self.findAction(MA.Delete);
		if(del){
			new Element('hr').inject(menu);
			link('Remove…', function(){
				del.showConfirm({'stopPropagation': function(){}});
			}, 'bad');
		}
	},

	createPicker: function(label, items, current, on_pick){
		var self = this;

		var cur_text = function(){
			var t = 'None';
			items.each(function(i){ if(i.value == current) t = i.text; });
			return t;
		};

		var wrap = new Element('div.mdx-mwrap'),
			button = new Element('button.mdx-btn.quiet', {
				'type': 'button',
				'title': label + ': saved as soon as you pick',
				'events': {
					'click': function(e){
						(e).stop();
						self.toggleMenu(wrap);
					}
				}
			}).inject(wrap),
			menu = new Element('div.mdx-menu').inject(wrap);

		var fill = function(){
			button.set('html', '').adopt(
				document.createTextNode(label + ': ' + cur_text() + ' '),
				new Element('span.car', {'text': '▾'})
			);
			menu.empty();
			items.each(function(item){
				new Element('a', {
					'class': item.value == current ? 'cur' : '',
					'events': {
						'click': function(e){
							(e).stop();
							self.closeMenus();
							if(item.value == current) return;
							current = item.value;
							fill();
							on_pick(item);
						}
					}
				}).adopt(
					new Element('span.ck', {'text': item.value == current ? '✓' : ''}),
					document.createTextNode(item.text)
				).inject(menu);
			});
		};
		fill();

		return wrap;
	},

	toggleMenu: function(wrap){
		var open = wrap.hasClass('open');
		this.closeMenus();
		if(!open) wrap.addClass('open');
	},

	closeMenus: function(){
		if(this.wrap) this.wrap.getElements('.mdx-mwrap.open').removeClass('open');
	},

	toast: function(text){
		var self = this;
		if(!self.toast_el) self.toast_el = new Element('div.mdx-toast').inject(self.wrap);
		self.toast_el.set('text', text).addClass('on');
		if(self.toast_timer) clearRequestTimeout(self.toast_timer);
		self.toast_timer = requestTimeout(function(){ self.toast_el.removeClass('on'); }, 2600);
	},

	// ----- Trailer pop-up -----

	playTrailer: function(e){
		var self = this;
		if(e && e.stop) (e).stop();

		var show = function(video_id){
			self.closeTrailer();
			self.video = new Element('div.mdx-video', {
				'events': {
					'click': function(ev){
						if(ev.target == self.video) self.closeTrailer();
					}
				}
			}).grab(
				new Element('div.mdx-vbox').adopt(
					new Element('div.mdx-vh').adopt(
						new Element('b', {'text': self.titleWithYear(self.current_title)}),
						new Element('span', {'text': 'Trailer', 'styles': {'color': '#aaa'}}),
						new Element('button', {
							'type': 'button',
							'text': '✕ Close',
							'events': {'click': self.closeTrailer.bind(self)}
						})
					),
					new Element('iframe', {
						'src': 'https://www.youtube-nocookie.com/embed/' + video_id + '?rel=0&autoplay=1&iv_load_policy=3&vq=hd720',
						'allow': 'autoplay; fullscreen',
						'allowfullscreen': 'true'
					})
				)
			).inject(self.wrap);
		};

		if(self.video_id) return show(self.video_id);

		var trailer = self.findAction(MA.Trailer);
		if(trailer && trailer.video_id){
			self.video_id = trailer.video_id;
			return show(self.video_id);
		}

		self.trailer_btn.set('text', '▶ Looking…');
		Api.request('movie.trailer', {
			'data': {
				'identifier': self.movie.getIdentifier ? self.movie.getIdentifier() : self.movie.get('imdb')
			},
			'onComplete': function(json){
				if(json && json.success && json.video_id){
					self.video_id = json.video_id;
					self.trailer_btn.set('text', '▶ Trailer');
					show(self.video_id);
				}
				else {
					self.trailer_btn.set({'text': 'No trailer found', 'disabled': true});
					self.wrap.addClass('mdx-no-trailer');
				}
			}
		});
	},

	closeTrailer: function(){
		if(this.video){
			this.video.destroy();
			this.video = null;
		}
	},

	// ----- Plugin hooks (unchanged) -----

	addSection: function(name, section_el){
		var self = this;
		name = name.toLowerCase();

		self.sections_el.grab(
			self.sections[name] = new Element('div', {
				'class': 'section section_' + name
			}).grab(section_el)
		);
	},

	addButton: function(button){
		var self = this;

		self.buttons.grab(button);
	},

	open: function(){
		var self = this;

		self.el.addClass('show');
		document.onkeyup = self.keyup.bind(self);

		self.outer_click = function(){
			self.close();
		};

		App.addEvent('history.push', self.outer_click);

	},

	keyup: function(e) {
		if (e.keyCode == 27 /* Esc */) {
			if(this.video) this.closeTrailer();
			else if(this.wrap.getElement('.mdx-mwrap.open')) this.closeMenus();
			else this.close();
		}
	},

	close: function(){
		var self = this;

		var ended = function() {
			self.wrap.dispose();
			self.overlay.removeEventListener('transitionend', ended);
			document.onkeyup = null;
		};
		self.overlay.addEventListener('transitionend', ended, false);

		self.closeTrailer();
		self.closeMenus();
		self.el.removeClass('show');

		App.removeEvent('history.push', self.outer_click);
	}
});

MovieDetails.injectStyle = function(){
	if(document.id('movie_details_style')) return;
	new Element('style#movie_details_style', {'type': 'text/css', 'text': MovieDetailsStyle}).inject(document.head);
};
