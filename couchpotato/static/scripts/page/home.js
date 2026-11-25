// Home views (Settings -> Screens): Classic = today's Home untouched; Sections and Dashboard restyle the
// same lists with CSS, so every action, list and chart from Classic stays (nothing is re-implemented).
var HomeStyle = [
	'.hv{--acc:#ac0000;--off:#ebebeb;--line:#e2e2e2;--muted:#6a6a6a;--bg:#fff;--text:#000}',
	'.dark .hv{--acc:#f85c22;--off:#363636;--line:#404040;--muted:#a8a8a8;--bg:#2d2d2d;--text:#fff}',

	// Header with the switch. Classic shows only the switch, small, on its own line.
	'.hv-head{display:flex;align-items:center;flex-wrap:wrap;gap:8px 16px;padding:10px 20px 0}',
	'.hv-head h1{display:none;flex:1;margin:0;font-size:28px;font-weight:300;color:var(--text)}',
	'.hv-seg{display:inline-flex;margin-left:auto;border:1px solid var(--line);border-radius:4px;overflow:hidden;background:var(--bg)}',
	'.hv-seg button{border:0;background:transparent;color:var(--muted);font:inherit;font-size:12px;padding:5px 10px;cursor:pointer;white-space:nowrap}',
	'.hv-seg button.on{background:var(--acc);color:#fff}',
	'.hv:not(.hv-v-classic) .hv-head{padding:16px 24px 14px;border-bottom:1px solid var(--line);margin-bottom:16px}',
	'.hv:not(.hv-v-classic) .hv-head h1{display:block}',
	'.hv-tiles,.hv-more{display:none}',

	// Shared by Sections and Dashboard: smaller section titles, the description under it, "See all" on the right.
	'.hv:not(.hv-v-classic) .scroll_content > .movies,.hv:not(.hv-v-classic) .charts > .movies{position:relative;padding:0 24px;margin-bottom:22px}',
	'.hv:not(.hv-v-classic) .movies > h2{font-size:16px;font-weight:600;padding:0 90px 0 0;margin:0;line-height:22px;height:auto}',
	'.hv:not(.hv-v-classic) .movies > .description{position:static;float:none;display:block;font-size:12px;color:var(--muted);padding:2px 90px 8px 0;margin:0;text-align:left;line-height:1.4}',
	'.hv:not(.hv-v-classic) .movies > .description:empty{display:none}',
	'.hv:not(.hv-v-classic) .hv-more{display:block;position:absolute;right:24px;top:2px;font-size:12px;color:var(--acc);cursor:pointer}',
	'.hv-v-sections .movies.hv-snatched > .hv-more,.hv .movies:not(:has(.movie)) > .hv-more{display:none}',
	'.hv:not(.hv-v-classic) .charts > .refresh{padding:0 24px}',
	'.hv:not(.hv-v-classic) .big_search{margin-bottom:22px}',

	// ----- Sections: Snatched & Available as cards, every other list one row of posters -----
	'.hv-v-sections .list_list.hv-snatched .movie{background:var(--off);border-radius:6px;margin-bottom:8px;border:0}',
	'.hv-v-sections .list_list.hv-snatched .movie .inner{display:flex;align-items:center;padding:8px 12px;gap:12px}',
	'.hv-v-sections .list_list.hv-snatched .movie .poster_container{flex:none;width:36px;height:54px;position:relative;border-radius:3px;overflow:hidden}',
	'.hv-v-sections .list_list.hv-snatched .movie .poster{display:block;position:absolute;inset:0;background:center/cover no-repeat}',
	'.hv-v-sections .list_list.hv-snatched .movie .info{flex:1;min-width:0;padding:0}',
	'.hv-v-sections .list_list.hv-snatched .movie .title span{font-weight:600}',
	'.hv-v-sections .hv-row > div:last-child{display:flex;flex-wrap:nowrap;gap:12px;overflow:hidden;padding:0}',
	'.hv-v-sections .hv-row.hv-open > div:last-child{flex-wrap:wrap}',
	'.hv-v-sections .hv-row .movie{flex:none;width:120px !important;border:0 !important;margin:0 0 4px;display:block}',
	'.hv-v-sections .hv-row.list_list .movie .poster_container{position:relative;width:100%;padding-bottom:150%;border-radius:4px;overflow:hidden}',
	'.hv-v-sections .hv-row.list_list .movie .poster{display:block;position:absolute;inset:0;background:center/cover no-repeat;background-color:var(--off)}',
	'.hv-v-sections .hv-row.list_list .movie .info{display:block;padding:4px 0 0}',
	'.hv-v-sections .hv-row.list_list .movie .title{display:flex;gap:4px;font-size:12px}',
	'.hv-v-sections .hv-row.list_list .movie .title span{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
	'.hv-v-sections .hv-row.list_list .movie .title .year{flex:none;padding:0;width:auto}',
	'.hv-v-sections .hv-row.list_list .movie .quality{display:none}',

	// ----- Dashboard: counts, the search bar, then every list as a compact card -----
	'.page.hv-v-dashboard .scroll_content{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;padding:0 24px 24px;align-items:start}',
	'.hv-v-dashboard .scroll_content > .hv-head{grid-column:1/-1;margin:0 -24px 4px;order:-3}',
	'.hv-v-dashboard .hv-tiles{grid-column:1/-1;display:grid;grid-template-columns:repeat(4,1fr);gap:10px;order:-2}',
	'.hv-tile{display:block;background:var(--off);border-radius:6px;padding:14px;color:var(--text)}',
	'.hv-tile b{display:block;font-size:24px;font-weight:400}',
	'.hv-tile span{font-size:12px;color:var(--muted)}',
	// An empty list (e.g. nothing "Available soon") hides itself in Classic; same here, so it leaves no hole
	'.hv:not(.hv-v-classic) .movies.hv-row:not(:has(.movie)){display:none}',
	'.hv-v-dashboard .scroll_content > .big_search{grid-column:1/-1;order:-1;height:auto;margin:0;padding:0;background:transparent}',
	'.page.home.hv-v-dashboard .big_search .search_form{max-width:none;margin:0;padding:0;height:44px}',
	'.page.home.hv-v-dashboard .big_search .search_form .wrapper{top:0;left:0;right:0}',
	'.page.home.hv-v-dashboard .big_search .search_form .wrapper .input{height:44px}',
	'.page.home.hv-v-dashboard .big_search .search_form .wrapper .input input{font-size:15px;padding-right:44px;border:1px solid var(--line)}',
	'.page.home.hv-v-dashboard .big_search .search_form .icon-search{top:0;right:0;width:44px;height:44px;line-height:44px;font-size:1.2em}',
	'.hv-v-dashboard .charts{display:contents}',
	'.hv.hv-v-dashboard .charts > .refresh{display:contents}',
	'.hv-v-dashboard .charts > .refresh > span{grid-column:1/-1}',
	'.hv.hv-v-dashboard .scroll_content > .movies,.hv.hv-v-dashboard .charts > .movies{background:var(--off);border-radius:6px;padding:12px;margin:0;min-width:0}',
	'.hv-v-dashboard .scroll_content > .movies:empty{display:none}',
	'.hv.hv-v-dashboard .movies > h2{padding-right:64px}',
	'.hv.hv-v-dashboard .movies > .description{padding-right:0}',
	'.hv.hv-v-dashboard .hv-more{right:12px;top:14px}',
	'.hv-v-dashboard .movies > div:last-child{display:block;padding:0}',
	'.hv-v-dashboard .movies .movie{display:none;width:auto !important;border:0 !important;margin:0;padding:6px 0;background:transparent}',
	'.hv-v-dashboard .movies .movie:nth-child(-n+4),.hv-v-dashboard .movies.hv-open .movie{display:block}',
	'.hv-v-dashboard .movies .movie .inner{display:flex;align-items:center;gap:10px;transform:none}',
	'.hv-v-dashboard .movies .movie .poster_container{flex:none;width:28px;height:42px;padding:0;position:relative;border-radius:3px;overflow:hidden}',
	'.hv-v-dashboard .movies .movie .poster{display:block;position:absolute;inset:0;background:center/cover no-repeat;background-color:var(--bg)}',
	'.hv-v-dashboard .movies .movie .poster_container .actions{display:none}',
	'.hv-v-dashboard .movies .movie .info{flex:1;min-width:0;display:block;padding:0;position:static}',
	'.hv-v-dashboard .movies .movie .title{display:block;font-size:13px}',
	'.hv-v-dashboard .movies .movie .title span{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
	'.hv-v-dashboard .movies .movie .title .year{display:block;font-size:12px;color:var(--muted);padding:0;margin:0;position:static}',
	'.hv-v-dashboard .movies .movie .quality{font-size:10px}',

	// Phone
	'@media (max-width:480px){',
	'.hv:not(.hv-v-classic) .hv-head{padding:12px 12px 10px}',
	'.hv:not(.hv-v-classic) .hv-head h1{font-size:22px}',
	'.hv:not(.hv-v-classic) .scroll_content > .movies,.hv:not(.hv-v-classic) .charts > .movies{padding:0 12px}',
	'.hv:not(.hv-v-classic) .hv-more{right:12px}',
	'.hv-v-sections .hv-row .movie{width:100px !important}',
	'.page.hv-v-dashboard .scroll_content{padding:0 12px 16px;grid-template-columns:1fr}',
	'.hv-v-dashboard .scroll_content > .hv-head{margin:0 -12px 4px}',
	'.hv-v-dashboard .hv-tiles{grid-template-columns:repeat(2,1fr)}',
	'.hv.hv-v-dashboard .scroll_content > .movies,.hv.hv-v-dashboard .charts > .movies{padding:12px}',
	'}'
].join('');

Page.Home = new Class({

	Extends: PageBase,

	name: 'home',
	title: 'Manage new stuff for things and such',
	icon: 'home',

	indexAction: function () {
		var self = this;

		if(self.soon_list){

			// Reset lists
			self.available_list.update();
			if(self.view == 'dashboard') self.loadCounts();

			if(self.late_list)
				self.late_list.update();

			return;
		}

		self.createHeader();

		self.chain = new Chain();
		self.chain.chain(
			self.createAvailable.bind(self),
			self.createBigsearch.bind(self),
			self.createSoon.bind(self),
			self.createSuggestions.bind(self),
			self.createCharts.bind(self),
			self.createLate.bind(self),
			function(){ self.decorate(); }
		);

		self.chain.callChain();

	},

	// ----- Views: Classic / Sections / Dashboard -----

	views: [['sections', '\u2630 Sections'], ['dashboard', '\u25A6 Dashboard'], ['classic', '\u27F2 Classic']],

	createHeader: function(){
		var self = this;

		var screens = App.getOption('screens') || {};
		self.view = screens.home_view || 'classic';

		self.seg = new Element('div.hv-seg');
		self.views.each(function(v){
			new Element('button', {
				'type': 'button',
				'text': v[1],
				'data-v': v[0],
				'events': {
					'click': function(e){
						(e).stop();
						self.pickView(v[0]);
					}
				}
			}).inject(self.seg);
		});

		new Element('div.hv-head').adopt(
			new Element('h1', {'text': 'Home'}),
			self.seg
		).inject(self.content);

		var tile = function(key, label, url){
			return new Element('a.hv-tile', {'href': url, 'data-k': key}).adopt(
				new Element('b', {'text': '\u2013'}),
				new Element('span', {'text': label})
			);
		};
		self.tiles = new Element('div.hv-tiles').adopt(
			tile('wanted', 'Wanted', App.createUrl('movies')),
			tile('snatched', 'Snatched', App.createUrl('movies')),
			tile('available', 'Available', App.createUrl('movies')),
			tile('library', 'In library', App.createUrl('movies/manage'))
		).inject(self.content);

		self.el.addClass('hv');
		self.applyView();
	},

	pickView: function(view){
		var self = this;
		if(self.view == view) return;

		self.view = view;
		self.applyView();

		// Same setting as Settings -> Screens, so the choice sticks on every browser
		var screens = App.getOption('screens');
		if(screens) screens.home_view = view;

		Api.request('settings.save', {
			'data': {
				'section': 'screens',
				'name': 'home_view',
				'value': view
			}
		});
	},

	applyView: function(){
		var self = this;

		self.el.removeClass('hv-v-classic').removeClass('hv-v-sections').removeClass('hv-v-dashboard')
			.addClass('hv-v-' + self.view);
		self.seg.getElements('button').each(function(b){
			b[b.get('data-v') == self.view ? 'addClass' : 'removeClass']('on');
		});

		self.decorate();
		if(self.view == 'dashboard') self.loadCounts();
	},

	// Counts for the Dashboard tiles: media.list counts everything before it applies the limit.
	counts: {
		'wanted': {'status': 'active'},
		'snatched': {'release_status': 'snatched,downloaded,seeding'},
		'available': {'release_status': 'available', 'status': 'active'},
		'library': {'status': 'done'}
	},

	loadCounts: function(){
		var self = this;

		Object.each(self.counts, function(filter, key){
			Api.request('media.list', {
				'data': Object.merge({'type': 'movie', 'limit_offset': '1'}, filter),
				'onComplete': function(json){
					var b = self.tiles.getElement('[data-k=' + key + '] b');
					if(b && json && json.total !== undefined) b.set('text', json.total);
				}
			});
		});
	},

	// "See all" on every list (charts arrive later, so this runs again when they do)
	decorate: function(){
		var self = this;

		if(self.available_list) $(self.available_list).addClass('hv-snatched');
		self.content.getElements('.movies').each(function(list){
			if(!list.hasClass('hv-snatched')) list.addClass('hv-row');
			if(!list.getElement('> .hv-more')){
				new Element('a.hv-more', {
					'text': 'See all \u203A',
					'events': {
						'click': function(e){
							(e).stop();
							list.toggleClass('hv-open');
							this.set('text', list.hasClass('hv-open') ? 'Show less \u2039' : 'See all \u203A');
						}
					}
				}).inject(list, 'top');
			}
		});
	},

	createBigsearch: function(){
		var self = this;

		new Element('.big_search').grab(
			new BlockSearch(self, {
				'animate': false
			})
		).inject(self.content);

		self.chain.callChain();
	},

	createAvailable: function(){
		var self = this;

		self.available_list = new MovieList({
			'navigation': false,
			'identifier': 'snatched',
			'load_more': false,
			'view': 'list',
			'actions': [MA.MarkAsDone, MA.IMDB, MA.Release, MA.Trailer, MA.Refresh, MA.Readd, MA.Delete, MA.Category, MA.Profile],
			'title': 'Snatched & Available',
			'description': 'These movies have been snatched or have finished downloading',
			'on_empty_element': new Element('div').adopt(
				new Element('h2', {'text': 'Snatched & Available'}),
				new Element('span.no_movies', {
					'html': 'No snatched movies or anything!? Damn.. <a href="#">Maybe add a movie.</a>',
					'events': {
						'click': function(e){
							(e).preventDefault();
							$(document.body).getElement('.big_search input').focus();
						}
					}
				})
			),
			'filter': {
				'release_status': 'snatched,missing,available,downloaded,done,seeding',
				'with_tags': 'recent'
			},
			'limit': null,
			'onLoaded': function(){
				self.chain.callChain();
			},
			'onMovieAdded': function(notification){

				// Track movie added
				var after_search = function(data){
					if(notification.data._id != data.data._id) return;

					// Force update after search
					self.available_list.update();
					App.off('movie.searcher.ended', after_search);
				};
				App.on('movie.searcher.ended', after_search);

			}
		});

		$(self.available_list).inject(self.content);

	},

	createSoon: function(){
		var self = this;

		// Coming Soon
		self.soon_list = new MovieList({
			'navigation': false,
			'identifier': 'soon',
			'limit': 12,
			'title': 'Available soon',
			'description': 'Should be available soon as they will be released on DVD/Blu-ray in the coming weeks.',
			'filter': {
				'random': true
			},
			'actions': [MA.IMDB, MA.Release, MA.Trailer, MA.Refresh, MA.Delete, MA.Category, MA.Profile],
			'load_more': false,
			'view': 'thumb',
			'force_view': true,
			'api_call': 'dashboard.soon',
			'onLoaded': function(){
				self.chain.callChain();
			}
		});

		$(self.soon_list).inject(self.content);

	},

	createSuggestions: function(){
		var self = this;

		self.suggestions_list = new MovieList({
			'navigation': false,
			'identifier': 'suggest',
			'limit': 12,
			'title': 'Suggestions',
			'description': 'Based on your current wanted and managed items',
			'actions': [MA.Add, MA.SuggestIgnore, MA.SuggestSeen, MA.IMDB, MA.Trailer],
			'load_more': false,
			'view': 'thumb',
			'force_view': true,
			'api_call': 'suggestion.view',
			'onLoaded': function(){
				self.chain.callChain();
			}
		});

		$(self.suggestions_list).inject(self.content);

	},

	createCharts: function(){
		var self = this;

		// Charts
		self.charts_list = new Charts({
			'onCreated': function(){
				self.chain.callChain();
			},
			'onLoaded': function(){
				self.decorate();
			}
		});

		$(self.charts_list).inject(self.content);

	},

	createLate: function(){
		var self = this;

		// Still not available
		self.late_list = new MovieList({
			'navigation': false,
			'identifier': 'late',
			'limit': 50,
			'title': 'Still not available',
			'description': 'Try another quality profile or maybe add more providers in <a href="' + App.createUrl('settings/searcher/providers/') + '">Settings</a>.',
			'filter': {
				'late': true
			},
			'loader': false,
			'load_more': false,
			'view': 'list',
			'actions': [MA.IMDB, MA.Trailer, MA.Refresh, MA.Delete, MA.Category, MA.Profile],
			'api_call': 'dashboard.soon',
			'onLoaded': function(){
				self.chain.callChain();
			}
		});

		$(self.late_list).inject(self.content);

	}

});

window.addEvent('domready', function(){
	if(!document.head) return;
	new Element('style#home_views_style', {'type': 'text/css', 'text': HomeStyle}).inject(document.head);
});
