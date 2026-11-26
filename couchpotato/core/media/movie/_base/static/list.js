var MovieList = new Class({

	Implements: [Events, Options],

	options: {
		api_call: 'media.list',
		navigation: true,
		limit: 50,
		load_more: true,
		loader: true,
		menu: [],
		add_new: false,
		force_view: false
	},

	available_views: ['thumb', 'list'],
	movies: [],
	movies_added: {},
	total_movies: 0,
	letters: {},
	filter: null,

	initialize: function(options){
		var self = this;
		self.setOptions(options);

		self.offset = 0;
		self.filter = self.options.filter || {
			'starts_with': null,
			'search': null
		};

		self.el = new Element('div.movies').adopt(
			self.title = self.options.title ? new Element('h2', {
				'text': self.options.title,
				'styles': {'display': 'none'}
			}) : null,
			self.description = self.options.description ? new Element('div.description', {
				'html': self.options.description,
				'styles': {'display': 'none'}
			}) : null,
			self.movie_list = new Element('div', {
				'events': {
					'click:relay(.movie)': function(e, el){
						el.retrieve('klass').onClick(e);
					},
					'mouseenter:relay(.movie)': function(e, el){
						(e).stopPropagation();
						el.retrieve('klass').onMouseenter(e);
					},
					'change:relay(.movie input)': function(e, el){
						(e).stopPropagation();
						el = el.getParent('.movie');
						var klass = el.retrieve('klass');
						klass.fireEvent('select');
						klass.select(klass.select_checkbox.get('checked'));
					}
				}
			}),
			self.load_more = self.options.load_more ? new Element('a.load_more', {
				'events': {
					'click': self.loadMore.bind(self)
				}
			}) : null
		);

		self.changeView(self.getSavedView() || self.options.view || 'thumb');

		// Create the alphabet nav
		if(self.options.navigation)
			self.createNavigation();

		if(self.options.api_call)
			self.getMovies();

		App.on('movie.added', self.movieAdded.bind(self));
		App.on('movie.deleted', self.movieDeleted.bind(self));
	},

	movieDeleted: function(notification){
		var self = this;

		if(self.movies_added[notification.data._id]){
			self.movies.each(function(movie){
				if(movie.get('_id') == notification.data._id){
					movie.destroy();
					delete self.movies_added[notification.data._id];
					self.setCounter(self.counter_count-1);
					self.total_movies--;
				}
			});
		}

		self.checkIfEmpty();
	},

	movieAdded: function(notification){
		var self = this;

		self.fireEvent('movieAdded', notification);
		if(self.options.add_new && !self.movies_added[notification.data._id] && notification.data.status == self.options.status){
			window.scroll(0,0);
			self.createMovie(notification.data, 'top');
			self.setCounter(self.counter_count+1);

			self.checkIfEmpty();
		}
	},

	create: function(){
		var self = this;

		if(self.options.load_more){
			self.scrollspy = new ScrollSpy({
				container: self.el.getParent(),
				min: function(){
					return self.load_more.getCoordinates().top;
				},
				onEnter: self.loadMore.bind(self)
			});
		}

		self.created = true;
	},

	addMovies: function(movies, total){
		var self = this;


		if(!self.created) self.create();

		// do scrollspy
		if(movies.length < self.options.limit && self.scrollspy){
			self.load_more.hide();
			self.scrollspy.stop();
		}

		self.createMovie(movies, 'bottom');

		self.total_movies += total;
		self.setCounter(total);

		self.calculateSelected();
	},

	setCounter: function(count){
		var self = this;

		if(!self.navigation_counter) return;

		self.counter_count = count;
		self.navigation_counter.set('text', count === 1 ? '1 movie' : (count || 0) + ' movies');

		if (self.empty_message) {
			self.empty_message.destroy();
			self.empty_message = null;
		}

		if(self.total_movies && count === 0 && !self.empty_message){
			var message = (self.filter.search ? 'for "'+self.filter.search+'"' : '') +
				(self.filter.starts_with ? ' in <strong>'+self.filter.starts_with+'</strong>' : '');

			self.empty_message = new Element('.message', {
				'html': 'No movies found ' + message + '.<br/>'
			}).grab(
				new Element('a', {
					'text': 'Reset filter',
					'events': {
						'click': function(){
							self.filter = {
								'starts_with': null,
								'search': null
							};
							self.navigation_search_input.set('value', '');
							if(self.chip_els) self.markChip('all');
							self.reset();
							self.activateLetter();
							self.getMovies(true);
							self.last_search_value = '';
						}
					}
				})
			).inject(self.movie_list);

		}

	},

	createMovie: function(movie, inject_at, nr){
		var self = this,
			movies = Array.isArray(movie) ? movie : [movie],
			movie_els = [];
		inject_at = inject_at || 'bottom';

		movies.each(function(movie, nr){

			var m = new Movie(self, {
				'actions': self.options.actions,
				'view': self.current_view,
				'onSelect': self.calculateSelected.bind(self)
			}, movie);

			var el = $(m);
			if(self.options.screens) self.addColumns(m, movie);

			if(inject_at === 'bottom'){
				movie_els.push(el);
			}
			else {
				el.inject(self.movie_list, inject_at);
			}

			self.movies.include(m);
			self.movies_added[movie._id] = true;
		});

		if(movie_els.length > 0){
			$(self.movie_list).adopt(movie_els);
		}

	},

	createNavigation: function(){
		var self = this;
		var chars = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ';

		self.el.addClass('with_navigation');

		self.navigation = new Element('div.alph_nav').adopt(
			self.mass_edit_form = new Element('div.mass_edit_form').adopt(
				new Element('span.select').adopt(
					self.mass_edit_select = new Element('input[type=checkbox]', {
						'events': {
							'change': self.massEditToggleAll.bind(self)
						}
					}),
					self.mass_edit_selected = new Element('span.count', {'text': 0}),
					self.mass_edit_selected_label = new Element('span', {'text': 'selected'})
				),
				new Element('div.quality').adopt(
					self.mass_edit_quality = new Element('select'),
					new Element('a.button.orange', {
						'text': 'Change quality',
						'events': {
							'click': self.changeQualitySelected.bind(self)
						}
					})
				),
				new Element('div.delete').adopt(
					new Element('span[text=or]'),
					new Element('a.button.red', {
						'text': 'Delete',
						'events': {
							'click': self.deleteSelected.bind(self)
						}
					})
				),
				new Element('div.refresh').adopt(
					new Element('span[text=or]'),
					new Element('a.button.green', {
						'text': 'Refresh',
						'events': {
							'click': self.refreshSelected.bind(self)
						}
					})
				)
			),
			new Element('div.menus').adopt(
				self.navigation_counter = new Element('span.counter[title=Total]'),
				self.filter_menu = new BlockMenu(self, {
					'class': 'filter',
					'button_class': 'icon-filter'
				}),
				self.navigation_actions = new Element('div.actions', {
					'events': {
						'click': function(e, el){
							(e).preventDefault();

							var new_view = self.current_view == 'list' ? 'thumb' : 'list';

							var a = 'active';
							self.navigation_actions.getElements('.'+a).removeClass(a);
							self.changeView(new_view);

							self.navigation_actions.getElement('[data-view='+new_view+']')
								.addClass(a);

						}
					}
				}),
				self.navigation_menu = new BlockMenu(self, {
					'class': 'extra',
					'button_class': 'icon-dots'
				})
			)
		);

		// Mass edit
		Quality.getActiveProfiles().each(function(profile){
			new Element('option', {
				'value': profile.get('_id'),
				'text': profile.get('label')
			}).inject(self.mass_edit_quality);
		});

		self.filter_menu.addLink(
			self.navigation_search_input = new Element('input', {
				'title': 'Search through ' + self.options.identifier,
				'placeholder': 'Search through ' + self.options.identifier,
				'events': {
					'keyup': self.search.bind(self),
					'change': self.search.bind(self)
				}
			})
		).addClass('search icon-search');

		self.filter_menu.addEvent('open', function(){
			self.navigation_search_input.focus();
			if(self.navigation.isDisplayed() || self.navigation.isVisible())
				self.loadAvailableChars();
		});

		self.filter_menu.addLink(
			self.navigation_alpha = new Element('ul.numbers', {
				'events': {
					'click:relay(li.available)': function(e, el){
						self.activateLetter(el.get('data-letter'));
						self.getMovies(true);
					}
				}
			})
		);

		// Actions
		['thumb', 'list'].each(function(view){
			var current = self.current_view == view;
			new Element('a', {
				'class': 'icon-' + view + (current ?  ' active ' : ''),
				'data-view': view
			}).inject(self.navigation_actions, current ? 'top' : 'bottom');
		});

		// All
		self.letters.all = new Element('li.letter_all.available.active', {
			'text': 'ALL'
		}).inject(self.navigation_alpha);

		// Chars
		chars.split('').each(function(c){
			self.letters[c] = new Element('li', {
				'text': c,
				'class': 'letter_'+c,
				'data-letter': c
			}).inject(self.navigation_alpha);
		});

		// Add menu or hide
		self.menu_lis = [];
		if (self.options.menu.length > 0)
			self.options.menu.each(function(menu_item){
				self.menu_lis.push([menu_item, self.navigation_menu.addLink(menu_item)]);
			});
		else
			self.navigation_menu.hide();

		if(self.options.screens)
			self.createViews();

	},

	// Get available chars and highlight them in A-Z (once)
	loadAvailableChars: function(){
		var self = this;
		if(self.available_chars_loaded) return;
		self.available_chars_loaded = true;

		Api.request('media.available_chars', {
			'data': Object.merge({
				'status': self.options.status
			}, self.filter),
			'onSuccess': function(json){
				(json.chars || []).each(function(c){
					var letter = self.letters[c.capitalize()];
					if(letter) letter.addClass('available');
				});
			}
		});
	},

	// ----- Views (Settings -> Screens): Posters / List / Classic, for Wanted and Manage -----
	// Classic = today's page untouched. Posters and List MOVE the existing buttons, search box and A-Z
	// out of the menus into a visible row (Classic moves them back), so nothing is re-implemented.

	list_views: [['posters', '\u25A6 Posters'], ['list', '\u2630 List'], ['classic', '\u27F2 Classic']],

	createViews: function(){
		var self = this;

		var screens = App.getOption('screens') || {};
		self.screen_view = screens[self.options.screens] || 'classic';

		self.view_seg = new Element('div.wv-seg');
		self.list_views.each(function(v){
			new Element('button', {
				'type': 'button',
				'text': v[1],
				'data-v': v[0],
				'events': {
					'click': function(e){
						(e).stop();
						self.pickScreenView(v[0]);
					}
				}
			}).inject(self.view_seg);
		});

		self.view_tools = new Element('div.wv-tools').adopt(
			new Element('div.wv-top').adopt(
				self.view_buttons = new Element('div.wv-buttons'),
				self.view_seg
			),
			self.view_filter = new Element('div.wv-filter')
		).inject(self.el, 'top');

		if(self.options.status_chips) self.createChips();
		self.view_head = new Element('div.wv-head').adopt(
			new Element('span.wv-h-movie', {'text': 'Movie'}),
			self.columns().map(function(c){ return new Element('span.wv-c-' + c[0], {'text': c[1]}); })
		).inject(self.view_tools);

		self.el.addClass('wv').addClass('wv-' + self.options.identifier);
		self.search_li = self.navigation_search_input.getParent('li');
		self.alpha_li = self.navigation_alpha.getParent('li');
		self.applyScreenView();
	},

	// List view columns: [key, header]
	columns: function(){
		return this.options.identifier == 'manage' ?
			[['quality', 'Quality'], ['folder', 'Folder']] :
			[['quality', 'Quality'], ['status', 'Status'], ['added', 'Added'], ['searched', 'Last search']];
	},

	// What a Wanted movie is waiting on, from its releases
	movieStatus: function(movie){
		var st = (movie.releases || []).map(function(r){ return r.status; });
		if(st.some(function(x){ return ['snatched', 'downloaded', 'seeding', 'missing'].indexOf(x) > -1; }))
			return ['snatched', 'Snatched'];
		if(st.indexOf('available') > -1) return ['available', 'Available'];
		if(st.indexOf('done') > -1) return ['done', 'In library'];
		return ['wanted', 'Wanted'];
	},

	movieFolder: function(movie){
		var files = movie.files && movie.files.movie;
		if(!files || !files.length)
			(movie.releases || []).each(function(r){
				if(!files && r.files && r.files.movie && r.files.movie.length) files = r.files.movie;
			});
		if(!files || !files.length) return '';
		var f = files[0], cut = Math.max(f.lastIndexOf('/'), f.lastIndexOf('\\'));
		return cut > 0 ? f.substr(0, cut) : f;
	},

	addColumns: function(m, movie){
		var self = this,
			months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
			cols = new Element('div.wv-cols');

		var day = function(t){
			if(!t) return '—';
			var d = new Date(t * 1000);
			return d.getDate() + ' ' + months[d.getMonth()] + (d.getFullYear() != new Date().getFullYear() ? ' ' + d.getFullYear() : '');
		};
		var ago = function(t){
			if(!t) return 'never';
			var s = Math.max(0, Date.now() / 1000 - t);
			if(s < 3600) return Math.max(1, Math.round(s / 60)) + ' min ago';
			if(s < 86400) return Math.round(s / 3600) + ' h ago';
			return Math.round(s / 86400) + ' d ago';
		};

		self.columns().each(function(c){
			var cell = new Element('span.wv-c-' + c[0]);
			if(c[0] == 'quality'){
				// the movie's own quality tags, shown as one cell
				var q = m.quality ? m.quality.getElements('span') : [];
				var done = q.filter(function(x){ return x.hasClass('done') || x.hasClass('snatched') || x.hasClass('available'); });
				var pick = done.length ? done[0] : q[0];
				cell.set('text', pick ? pick.get('text') : '');
			}
			else if(c[0] == 'status'){
				var st = self.movieStatus(movie);
				cell.adopt(new Element('span.wv-pill.wv-s-' + st[0], {'text': st[1]}));
			}
			else if(c[0] == 'added') cell.set('text', day(movie.added));
			else if(c[0] == 'searched') cell.set('text', ago(movie.last_search));
			else if(c[0] == 'folder'){
				var folder = self.movieFolder(movie);
				cell.set({'text': folder, 'title': folder});
			}
			cols.grab(cell);
		});

		var info = $(m).getElement('.info');
		if(info) cols.inject(info, 'after');
	},

	// Wanted: All / Snatched / Available / Still wanted, with counts
	chips: [
		['all', 'All', {}],
		['snatched', 'Snatched', {'release_status': 'snatched,downloaded,seeding,missing'}],
		['available', 'Available', {'release_status': 'available'}],
		['still', 'Still wanted', {'no_release_status': 'snatched,downloaded,seeding,missing,available'}]
	],

	createChips: function(){
		var self = this;
		self.chip = 'all';
		self.chip_els = {};
		self.view_chips = new Element('div.wv-chips');

		self.chips.each(function(c){
			self.chip_els[c[0]] = new Element('button', {
				'type': 'button',
				'class': c[0] == 'all' ? 'on' : '',
				'data-chip': c[0],
				'events': {
					'click': function(e){
						(e).stop();
						self.pickChip(c[0]);
					}
				}
			}).adopt(
				new Element('span', {'text': c[1]}),
				new Element('em')
			).inject(self.view_chips);
		});

		self.view_chips.inject(self.view_filter);
		self.loadChipCounts();
		self.addEvent('loaded', function(){
			// counts follow adds, deletes and searches that reload the list
			if(self.chip_counts_at && Date.now() - self.chip_counts_at > 3000) self.loadChipCounts();
		});
	},

	loadChipCounts: function(){
		var self = this;
		self.chip_counts_at = Date.now();
		self.chips.each(function(c){
			Api.request('media.list', {
				'data': Object.merge({
					'type': self.options.type || 'movie',
					'status': self.options.status,
					'limit_offset': 1
				}, c[2]),
				'onSuccess': function(json){
					self.chip_els[c[0]].getElement('em').set('text', json && json.total !== undefined ? json.total : '');
				}
			});
		});
	},

	pickChip: function(chip){
		var self = this;
		if(self.chip == chip) return;
		self.markChip(chip);

		delete self.filter.release_status;
		delete self.filter.no_release_status;
		self.chips.each(function(c){
			if(c[0] == chip) Object.merge(self.filter, c[2]);
		});
		self.reset();
		self.getMovies(true);
	},

	markChip: function(chip){
		var self = this;
		self.chip = chip;
		Object.each(self.chip_els, function(el, k){ el[k == chip ? 'addClass' : 'removeClass']('on'); });
	},

	pickScreenView: function(view){
		var self = this;
		if(self.screen_view == view) return;

		self.screen_view = view;
		self.applyScreenView();

		// Same setting as Settings -> Screens, so the choice sticks on every browser
		var screens = App.getOption('screens');
		if(screens) screens[self.options.screens] = view;

		Api.request('settings.save', {
			'data': {
				'section': 'screens',
				'name': self.options.screens,
				'value': view
			}
		});
	},

	applyScreenView: function(){
		var self = this,
			view = self.screen_view,
			classic = view == 'classic';

		self.el.removeClass('wv-v-classic').removeClass('wv-v-posters').removeClass('wv-v-list')
			.addClass('wv-v-' + view);
		self.navigation.removeClass('wv-v-classic').removeClass('wv-v-posters').removeClass('wv-v-list')
			.addClass('wv-v-' + view);
		self.view_seg.getElements('button').each(function(b){
			b[b.get('data-v') == view ? 'addClass' : 'removeClass']('on');
		});

		if(classic){
			self.navigation_search_input.inject(self.search_li);
			self.navigation_alpha.inject(self.alpha_li);
			self.menu_lis.each(function(m){ m[0].inject(m[1]); });
		}
		else {
			self.navigation_search_input.inject(self.view_filter);
			self.navigation_alpha.inject(self.view_filter);
			self.menu_lis.each(function(m){ m[0].inject(self.view_buttons); });
			self.loadAvailableChars();

			var want = view == 'posters' ? 'thumb' : 'list';
			if(self.current_view != want){
				self.changeView(want);
				self.navigation_actions.getElements('.active').removeClass('active');
				self.navigation_actions.getElement('[data-view=' + want + ']').addClass('active');
			}
		}
	},

	calculateSelected: function(){
		var self = this;

		var selected = 0,
			movies = self.movies.length;
		self.movies.each(function(movie){
			selected += movie.isSelected() ? 1 : 0;
		});

		var indeterminate = selected > 0 && selected < movies,
			checked = selected == movies && selected > 0;

		document.body[selected > 0 ? 'addClass' : 'removeClass']('mass_editing');

		if(self.mass_edit_select){
			self.mass_edit_select.set('checked', checked);
			self.mass_edit_select.indeterminate = indeterminate;

			self.mass_edit_selected.set('text', selected);
		}
	},

	deleteSelected: function(){
		var self = this,
			ids = self.getSelectedMovies(),
			help_msg = self.identifier == 'wanted' ? 'If you do, you won\'t be able to watch them, as they won\'t get downloaded!' : 'Your files will be safe, this will only delete the references in CouchPotato';

		var qObj = new Question('Are you sure you want to delete '+ids.length+' movie'+ (ids.length != 1 ? 's' : '') +'?', help_msg, [{
			'text': 'Yes, delete '+(ids.length != 1 ? 'them' : 'it'),
			'class': 'delete',
			'events': {
				'click': function(e){
					(e).preventDefault();
					this.set('text', 'Deleting..');
					Api.request('media.delete', {
						'method': 'post',
						'data': {
							'id': ids.join(','),
							'delete_from': self.options.identifier
						},
						'onSuccess': function(){
							qObj.close();

							var erase_movies = [];
							self.movies.each(function(movie){
								if (movie.isSelected()){
									$(movie).destroy();
									erase_movies.include(movie);
								}
							});

							erase_movies.each(function(movie){
								self.movies.erase(movie);
								movie.destroy();
								self.setCounter(self.counter_count-1);
								self.total_movies--;
							});

							self.calculateSelected();
						}
					});

				}
			}
		}, {
			'text': 'Cancel',
			'cancel': true
		}]);

	},

	changeQualitySelected: function(){
		var self = this;
		var ids = self.getSelectedMovies();

		Api.request('movie.edit', {
			'method': 'post',
			'data': {
				'id': ids.join(','),
				'profile_id': self.mass_edit_quality.get('value')
			},
			'onSuccess': self.search.bind(self)
		});
	},

	refreshSelected: function(){
		var self = this;
		var ids = self.getSelectedMovies();

		Api.request('media.refresh', {
			'method': 'post',
			'data': {
				'id': ids.join(',')
			}
		});
	},

	getSelectedMovies: function(){
		var self = this;

		var ids = [];
		self.movies.each(function(movie){
			if (movie.isSelected())
				ids.include(movie.get('_id'));
		});

		return ids;
	},

	massEditToggleAll: function(){
		var self = this;

		var select = self.mass_edit_select.get('checked');

		self.movies.each(function(movie){
			movie.select(select);
		});

		self.calculateSelected();
	},

	reset: function(){
		var self = this;

		self.movies = [];
		if(self.mass_edit_select)
			self.calculateSelected();
		if(self.navigation_alpha)
			self.navigation_alpha.getElements('.active').removeClass('active');

		self.offset = 0;
		if(self.scrollspy){
			//self.load_more.show();
			self.scrollspy.start();
		}
	},

	activateLetter: function(letter){
		var self = this;

		self.reset();

		self.letters[letter || 'all'].addClass('active');
		self.filter.starts_with = letter;

	},

	changeView: function(new_view){
		var self = this;

		if(self.available_views.indexOf(new_view) == -1)
			new_view = 'thumb';

		self.el
			.removeClass(self.current_view+'_list')
			.addClass(new_view+'_list');

		self.current_view = new_view;
		Cookie.write(self.options.identifier+'_view', new_view, {duration: 1000});
	},

	getSavedView: function(){
		var self = this;
		return self.options.force_view ? self.options.view : Cookie.read(self.options.identifier+'_view');
	},

	search: function(){
		var self = this;

		if(self.search_timer) clearRequestTimeout(self.search_timer);
		self.search_timer = requestTimeout(function(){
			var search_value = self.navigation_search_input.get('value');
			if (search_value == self.last_search_value) return;

			self.reset();

			self.activateLetter();
			self.filter.search = search_value;

			self.getMovies(true);

			self.last_search_value = search_value;

		}, 250);

	},

	update: function(){
		var self = this;

		self.reset();
		self.getMovies(true);
	},

	getMovies: function(reset){
		var self = this;

		if(self.scrollspy){
			self.scrollspy.stop();
			self.load_more.set('text', 'loading...');
		}

		var loader_timeout;
		if(self.movies.length === 0 && self.options.loader){

			self.loader_first = new Element('div.mask.loading.with_message').grab(
				new Element('div.message', {'text': self.options.title ? 'Loading \'' + self.options.title + '\'' : 'Loading...'})
			).inject(self.el, 'top');
			createSpinner(self.loader_first);

			var lfc = self.loader_first;
			loader_timeout = requestTimeout(function(){
				lfc.addClass('show');
			}, 10);

			self.el.setStyle('min-height', 220);

		}

		Api.request(self.options.api_call, {
			'data': Object.merge({
				'type': self.options.type || 'movie',
				'status': self.options.status,
				'limit_offset': self.options.limit ? self.options.limit + ',' + self.offset : null,
				'with_times': self.options.screens ? 1 : null
			}, self.filter),
			'onSuccess': function(json){

				if(reset)
					self.movie_list.empty();

				if(loader_timeout) clearRequestTimeout(loader_timeout);
				if(self.loader_first){
					var lf = self.loader_first;
					self.loader_first = null;
					lf.removeClass('show');

					requestTimeout(function(){
						lf.destroy();
					}, 1000);
					self.el.setStyle('min-height', null);
				}

				self.store(json.movies);
				self.addMovies(json.movies, json.total || json.movies.length);
				if(self.scrollspy) {
					self.load_more.set('text', 'load more movies');
					self.scrollspy.start();
				}

				self.checkIfEmpty();
				self.fireEvent('loaded');
			}
		});
	},

	loadMore: function(){
		var self = this;
		if(self.offset >= self.options.limit)
			self.getMovies();
	},

	store: function(movies){
		var self = this;

		self.offset += movies.length;

	},

	checkIfEmpty: function(){
		var self = this;

		var is_empty = self.movies.length === 0 && (self.total_movies === 0 || self.total_movies === undefined);

		if(self.title)
			self.title[is_empty ? 'hide' : 'show']();

		if(self.description)
			self.description.setStyle('display', [is_empty ? 'none' : '']);

		if(is_empty && self.options.on_empty_element){
			var ee = typeOf(self.options.on_empty_element) == 'function' ? self.options.on_empty_element() : self.options.on_empty_element;
			ee.inject(self.loader_first || self.title || self.movie_list, 'after');

			if(self.navigation)
				self.navigation.hide();

			self.empty_element = ee;
		}
		else if(self.empty_element){
			self.empty_element.destroy();

			if(self.navigation)
				self.navigation.show();
		}

	},

	toElement: function(){
		return this.el;
	}

});

// Styles for the Wanted / Manage views (see createViews)
var MovieListViewsStyle = [
	'.wv{--acc:#ac0000;--off:#ebebeb;--line:#e2e2e2;--muted:#6a6a6a;--bg:#fff;--text:#000}',
	'.dark .wv{--acc:#f85c22;--off:#363636;--line:#404040;--muted:#a8a8a8;--bg:#2d2d2d;--text:#fff}',
	'.wv-tools{padding:10px 20px 0}',
	'.wv-top{display:flex;align-items:center;flex-wrap:wrap;gap:8px}',
	'.wv-buttons{display:none;flex-wrap:wrap;gap:8px;flex:1}',
	'.wv-filter{display:none}',
	'.wv-seg{display:inline-flex;margin-left:auto;border:1px solid var(--line);border-radius:4px;overflow:hidden;background:var(--bg)}',
	'.wv-seg button{border:0;background:transparent;color:var(--muted);font:inherit;font-size:12px;padding:5px 10px;cursor:pointer;white-space:nowrap}',
	'.wv-seg button.on{background:var(--acc);color:#fff}',

	// New views: today's menus (filter, thumb/list, more) are replaced by the row
	'.alph_nav:not(.wv-v-classic) .more_menu.filter,.alph_nav:not(.wv-v-classic) .actions{display:none}',
	'.alph_nav:not(.wv-v-classic) .more_menu.extra{display:none}',
	'.wv:not(.wv-v-classic) .wv-tools{padding:16px 24px 6px}',
	'.wv:not(.wv-v-classic) .wv-buttons{display:flex}',
	'.wv-buttons a{display:inline-block;border:1px solid var(--acc);color:var(--acc);border-radius:4px;padding:6px 12px;font-size:13px;cursor:pointer;white-space:nowrap}',
	'.wv-buttons a:first-child{background:var(--acc);color:#fff}',
	'.wv:not(.wv-v-classic) .wv-filter{display:flex;flex-wrap:wrap;align-items:center;gap:8px 16px;margin-top:14px}',
	'.wv-filter input{width:240px;max-width:100%;border:1px solid var(--line);border-radius:4px;padding:8px 10px;font-size:14px;background:var(--bg);color:var(--text)}',
	'.wv-filter ul.numbers{display:flex;flex-wrap:wrap;gap:2px;margin:0;padding:0;list-style:none;font-size:11px}',
	'.wv-filter ul.numbers li{padding:3px 4px;color:var(--muted);opacity:.45;cursor:default}',
	'.wv-filter ul.numbers li.available{opacity:1;cursor:pointer}',
	'.wv-filter ul.numbers li.active{color:var(--acc);font-weight:700}',

	// Status chips (Wanted)
	'.wv-chips{display:flex;flex-wrap:wrap;gap:6px}',
	'.wv-chips button{border:1px solid var(--line);background:var(--bg);color:var(--text);border-radius:14px;padding:5px 12px;font:inherit;font-size:12px;cursor:pointer;white-space:nowrap}',
	'.wv-chips button em{font-style:normal;margin-left:5px;color:var(--muted)}',
	'.wv-chips button.on{background:var(--acc);border-color:var(--acc);color:#fff}',
	'.wv-chips button.on em{color:#fff}',
	'.wv-filter ul.numbers{flex-basis:100%}',

	// List columns (hidden in Posters and Classic)
	'.wv-head,.wv .wv-cols{display:none}',
	'.wv-v-list .wv-head{display:flex;gap:12px;margin:12px 0 -8px;padding:0 0 6px 63px;border-bottom:1px solid var(--line);font-size:11px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}',
	'.wv-v-list .wv-head .wv-h-movie{flex:1}',
	'.wv-v-list.list_list .movie .wv-cols{display:flex;gap:12px;align-items:center;font-size:13px}',
	'.wv-v-list .wv-c-quality{width:80px}',
	'.wv-v-list .wv-c-status{width:100px}',
	'.wv-v-list .wv-c-added{width:80px}',
	'.wv-v-list .wv-c-searched{width:90px}',
	'.wv-v-list .wv-c-folder{width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--muted);font-size:12px}',
	'.wv-v-list.list_list .movie .info .quality,.wv-v-list.list_list .movie .info .rating{display:none}',
	'.wv-pill{display:inline-block;border-radius:3px;padding:2px 7px;font-size:11px;font-weight:700;background:var(--off);color:var(--muted)}',
	'.wv-pill.wv-s-snatched{background:#e3effd;color:#1a5fb4}',
	'.wv-pill.wv-s-available{background:#e3f6e6;color:#1d7a33}',
	'.wv-pill.wv-s-done{background:#e3f6e6;color:#1d7a33}',
	'.dark .wv-pill.wv-s-snatched{background:#1f3550;color:#9cc7ff}',
	'.dark .wv-pill.wv-s-available,.dark .wv-pill.wv-s-done{background:#1f3d27;color:#8fdc9f}',

	// Posters
	'.wv-v-posters.thumb_list > div:last-of-type{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:14px;padding:12px 24px}',
	'.wv-v-posters.thumb_list .movie{width:auto !important;border:0 !important;margin:0}',
	'.wv-v-posters.thumb_list .movie .info .title{font-size:13px}',
	'.wv-v-posters.thumb_list .movie .info .quality{display:flex;flex-wrap:wrap;gap:2px;white-space:normal;height:auto}',

	// List
	'.wv-v-list.list_list > div:last-of-type{padding:8px 24px}',
	'.wv-v-list.list_list .movie{border-bottom:1px solid var(--line)}',
	'.wv-v-list.list_list .movie .inner{display:flex;align-items:center;gap:12px;padding:6px 0}',
	'.wv-v-list.list_list .movie .poster_container{flex:none;width:26px;height:39px;position:relative;border-radius:3px;overflow:hidden}',
	'.wv-v-list.list_list .movie .poster{display:block;position:absolute;inset:0;background:center/cover no-repeat;background-color:var(--off)}',
	'.wv-v-list.list_list .movie .poster_container .actions{display:none}',
	'.wv-v-list.list_list .movie .info{flex:1;min-width:0;padding:0 8px 0 0}',
	'.wv-v-list.list_list .movie .title span{font-weight:600;margin-left:0 !important}',
	// mass edit: the checkbox gets its own column instead of sitting on the poster
	'.wv-v-list.list_list .movie input[type=checkbox]{position:static;transform:none;flex:none;margin:0}',

	'@media (max-width:480px){',
	'.wv:not(.wv-v-classic) .wv-tools{padding:12px 12px 4px}',
	'.wv-filter input{width:100%}',
	'.wv-v-posters.thumb_list > div:last-of-type{grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:10px;padding:10px 12px}',
	'.wv-v-list.list_list > div:last-of-type{padding:6px 12px}',
	'.wv-v-list .wv-head{padding-left:0}',
	'.wv-v-list .wv-head span:not(.wv-h-movie),.wv-v-list .wv-c-added,.wv-v-list .wv-c-searched,.wv-v-list .wv-c-quality{display:none}',
	'.wv-v-list .wv-c-folder{width:120px}',
	'}'
].join('');

window.addEvent('domready', function(){
	if(!document.head) return;
	new Element('style#movie_list_views_style', {'type': 'text/css', 'text': MovieListViewsStyle}).inject(document.head);
});
