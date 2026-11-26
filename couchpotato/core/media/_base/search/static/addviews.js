// Add a movie: Dropdown / Full page / Classic (Settings -> Screens, or the switch above the results).
// Classic is the old CouchPotato search, untouched. Dropdown restyles the same result rows (best 4 + "View all N
// results"). Full page moves the same result elements into a page-sized panel as a poster grid with one-click
// "+ Add" (adds with the chosen quality profile). Nothing is fetched twice: BlockSearch still owns the request.

var AddViewsStyle = [
	'.av-seg{display:flex;justify-content:flex-end;gap:0;padding:6px 8px;font-size:12px}',
	'.av-seg span{display:inline-flex;border:1px solid #e2e2e2;border-radius:4px;overflow:hidden}',
	'.dark .av-seg span{border-color:#404040}',
	'.av-seg button{border:0;background:transparent;color:inherit;opacity:.75;font:inherit;padding:4px 9px;cursor:pointer;white-space:nowrap}',
	'.av-seg button.on{background:#ac0000;color:#fff;opacity:1}',
	'.dark .av-seg button.on{background:#f85c22}',
	'.search_form .av-more{display:none;text-align:center;padding:10px;font-weight:600;color:#ac0000;cursor:pointer;border-top:1px solid rgba(0,0,0,.08)}',
	'.dark .search_form .av-more{color:#f85c22}',
	'.media_result .av-add,.media_result .av-pill{display:none}',
	// Dropdown: best 4 rows, taller, green "Already in" line
	'.search_form.av-dropdown .results{max-height:none !important}',
	'.search_form.av-dropdown .results .media_result:nth-child(n+5){display:none}',
	'.search_form.av-dropdown.av-many .av-more{display:block}',
	'.search_form.av-dropdown .media_result .in_wanted,.search_form.av-dropdown .media_result .in_library{color:#1e7d32 !important;opacity:1 !important}',
	// Full page panel
	'.av-page{position:fixed;top:0;right:0;bottom:0;left:132px;z-index:30;overflow:auto;padding:20px 24px 40px;background:#fff;color:#000;text-align:left}',
	'.dark .av-page{background:#2d2d2d;color:#fff}',
	'.av-page .av-top{display:flex;align-items:center;gap:12px;margin-bottom:14px}',
	'.av-page h1{font-size:28px;font-weight:300;margin:0;flex:1}',
	'.av-page .av-close{border:0;background:transparent;color:inherit;font-size:22px;cursor:pointer;padding:4px 8px}',
	'.av-page .av-seg{padding:0}',
	'.av-page .av-q{width:100%;box-sizing:border-box;font-size:16px;padding:10px 12px;border:1px solid #ddd;border-radius:3px;background:inherit;color:inherit}',
	'.dark .av-page .av-q{border-color:#555}',
	'.av-page .av-with{font-size:12.5px;opacity:.8;margin:6px 0 14px}',
	'.av-page .av-with a{color:#ac0000;cursor:pointer;margin-left:4px}',
	'.dark .av-page .av-with a{color:#f85c22}',
	'.av-page .av-with select{margin-left:6px;font-size:12.5px}',
	'.av-page .av-msg{padding:20px 0;opacity:.7}',
	'.av-page .results{display:grid;grid-template-columns:repeat(auto-fill,minmax(116px,1fr));gap:18px 14px;max-height:none}',
	'.av-page .media_result{height:auto !important;overflow:visible !important;position:relative;cursor:default;display:flex;flex-direction:column;background:none !important;border:0 !important}',
	'.av-page .media_result .thumbnail{position:static !important;width:100% !important;height:auto !important;aspect-ratio:2/3;object-fit:cover;border-radius:3px;display:block;margin:0 0 6px !important;cursor:pointer}',
	'.av-page .media_result .data{position:static !important;left:auto !important;padding:0 !important;background:none !important;height:auto !important;border:0 !important}',
	'.av-page .media_result .info{position:static !important;height:auto !important;padding:0 !important}',
	'.av-page .media_result h2{font-size:13px !important;font-weight:400 !important;margin:0 !important;white-space:normal !important;height:auto !important;line-height:1.3 !important;display:flex;flex-wrap:wrap;align-items:center;gap:4px 6px}',
	'.av-page .media_result h2 .title{flex:1 0 100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
	'.av-page .media_result h2 .year{opacity:.7;font-size:12.5px;margin:0 !important;position:static !important}',
	'.av-page .media_result .in_wanted,.av-page .media_result .in_library{display:none !important}',
	'.av-page .media_result .av-pill{display:inline-block;font-size:11px;font-weight:600;padding:1px 6px;border-radius:3px;background:#e8e8e8;color:#333}',
	'.av-page .media_result .av-pill.lib{background:#dff3e1;color:#1e7d32}',
	'.av-page .media_result .av-add{display:inline-block;font-size:12.5px;padding:2px 8px;border:1px solid #ac0000;border-radius:3px;color:#ac0000;cursor:pointer;white-space:nowrap}',
	'.dark .av-page .media_result .av-add{border-color:#f85c22;color:#f85c22}',
	'.av-page .media_result .av-add.busy{opacity:.5;pointer-events:none}',
	'.av-page .media_result .options{position:static !important;height:auto !important;margin-top:6px;font-size:12px}',
	'.av-page .media_result .options:empty{display:none}',
	'.av-page .media_result .options > div{display:flex;flex-direction:column;gap:4px}',
	'.av-page .media_result .options select{width:100%;max-width:100%}',
	'.av-page .media_result .data .options{display:none}',
	'@media (max-width:480px){',
	'.av-page{left:0;padding:14px 12px 30px}',
	'.av-page h1{font-size:22px}',
	'.av-page .av-top{flex-wrap:wrap}',
	'.av-page .results{grid-template-columns:repeat(auto-fill,minmax(100px,1fr))}',
	'}'
].join('');

var AddViews = {

	VIEWS: [['dropdown', '▾ Dropdown'], ['fullpage', '▦ Full page'], ['classic', '↺ Classic']],
	blocks: [],

	view: function(){
		return (App.getOption('screens') || {}).add_view || 'classic';
	},

	style: function(){
		if(AddViews.styled) return;
		AddViews.styled = true;
		new Element('style#addviews_style', {'type': 'text/css', 'text': AddViewsStyle}).inject(document.head);
	},

	segment: function(){
		var seg = new Element('div.av-seg'), span = new Element('span').inject(seg);
		AddViews.VIEWS.each(function(v){
			new Element('button', {
				'type': 'button', 'text': v[1], 'data-view': v[0],
				'events': {
					'mousedown': function(e){ (e).stop(); },  // keep the search box focused
					'click': function(e){ (e).stop(); AddViews.pick(v[0]); }
				}
			}).inject(span);
		});
		return seg;
	},

	markSegments: function(){
		$$('.av-seg button').each(function(b){
			b[b.get('data-view') == AddViews.view() ? 'addClass' : 'removeClass']('on');
		});
	},

	// Called once per BlockSearch (the header one and Home's big one)
	attach: function(block){
		AddViews.style();
		AddViews.blocks.push(block);
		block.result_container.grab(AddViews.segment(), 'top');
		block.av_more = new Element('div.av-more', {
			'events': {
				'mousedown': function(e){ (e).stop(); },
				'click': function(e){ (e).stop(); AddViews.openPage(block, true); }
			}
		}).inject(block.result_container);
		AddViews.apply(block);
	},

	apply: function(block){
		var view = AddViews.view();
		block.el.removeClass('av-dropdown').removeClass('av-fullpage').removeClass('av-classic').addClass('av-' + view);
		AddViews.markSegments();
	},

	pick: function(view){
		var screens = App.getOption('screens');
		if(screens) screens.add_view = view;
		// Same setting as Settings -> Screens, so the choice sticks on every browser
		Api.request('settings.save', {'data': {'section': 'screens', 'name': 'add_view', 'value': view}});

		var open = AddViews.page_block;
		AddViews.blocks.each(AddViews.apply);
		if(view == 'fullpage'){
			var block = open || AddViews.blocks.filter(function(b){ return b.q(); })[0];
			if(block) AddViews.openPage(block, false);
		}
		else if(open){
			AddViews.closePage();
			if(open.q()){
				open.el.addClass('focused');
				open.hideResults(false);
				open.input.focus();
			}
		}
	},

	// After BlockSearch.fill drew the result rows
	filled: function(block, q){
		var n = block.results.getElements('.media_result').length;
		block.el[n > 4 ? 'addClass' : 'removeClass']('av-many');
		block.av_more.set('text', 'View all ' + n + ' results ›');
		if(AddViews.view() == 'fullpage' || AddViews.page_block == block)
			AddViews.openPage(block, false);
	},

	profile: function(){
		var profiles = Quality.getActiveProfiles();
		var found = profiles.filter(function(p){ return p.get('_id') == AddViews.profile_id; })[0];
		return found || profiles[0];
	},

	openPage: function(block, all){
		var self = AddViews;
		if(!self.page) self.buildPage();
		if(self.page_block && self.page_block != block) self.closePage();
		self.page_block = block;

		self.page.q.set('value', block.q());
		self.page.grid.grab(block.results);  // the same result elements, moved
		var n = block.results.getElements('.media_result').length;
		self.page.msg.set('text', block.q() ? (n ? '' : 'Nothing found for “' + block.q() + '”') : 'Type a movie name');
		self.page.msg.setStyle('display', n && block.q() ? 'none' : '');
		self.fillWith();
		self.page.el.setStyle('display', '');
		block.hideResults(true);
		block.el.removeClass('focused');
		document.body.addClass('av-page-open');
		if(!self.page.q.retrieve('focused_once')){
			self.page.q.store('focused_once', true);
		}
		self.page.q.focus();
	},

	closePage: function(){
		var self = AddViews, block = self.page_block;
		if(!block) return;
		block.result_container.grab(block.results, 'top');
		block.result_container.grab(block.result_container.getElement('.av-seg'), 'top');
		block.av_more.inject(block.result_container);
		self.page.el.setStyle('display', 'none');
		self.page_block = null;
		document.body.removeClass('av-page-open');
	},

	fillWith: function(){
		var self = AddViews, profile = self.profile(), w = self.page.with_el;
		w.empty();
		if(!profile) return;
		w.adopt(
			new Element('span', {'text': 'Adds with '}),
			new Element('b', {'text': profile.get('label')}),
			new Element('span', {'text': ' ·'}),
			new Element('a', {
				'text': 'change',
				'events': {'click': function(){
					w.empty();
					var sel = new Element('select', {'events': {'change': function(){
						self.profile_id = this.get('value');
						self.fillWith();
					}}});
					Quality.getActiveProfiles().each(function(p){
						new Element('option', {'value': p.get('_id'), 'text': p.get('label'),
							'selected': p.get('_id') == profile.get('_id')}).inject(sel);
					});
					w.adopt(new Element('span', {'text': 'Adds with'}), sel);
				}}
			})
		);
	},

	buildPage: function(){
		var self = AddViews, timer;
		var p = self.page = {};
		p.el = new Element('div.av-page', {'styles': {'display': 'none'}}).adopt(
			new Element('div.av-top').adopt(
				new Element('h1', {'text': 'Add a movie'}),
				self.segment(),
				new Element('button.av-close', {'type': 'button', 'text': '✕', 'title': 'Close',
					'events': {'click': function(){ self.closePage(); }}})
			),
			p.q = new Element('input.av-q', {
				'type': 'text', 'placeholder': 'Search & add a new movie',
				'events': {'input': function(){
					var block = self.page_block, value = this.get('value');
					if(!block) return;
					if(timer) clearRequestTimeout(timer);
					timer = requestTimeout(function(){
						block.input.set('value', value);
						block.keyup();
					}, 50);
				}, 'keydown': function(e){
					if(e.key == 'esc') self.closePage();
				}}
			}),
			p.with_el = new Element('div.av-with'),
			p.msg = new Element('div.av-msg'),
			p.grid = new Element('div.av-grid')
		).inject(document.body);
		self.markSegments();
		History.addEvent('change', function(){ self.closePage(); });
		document.addEvent('keydown', function(e){
			if(e.key == 'esc' && self.page_block) self.closePage();
		});
	}
};
