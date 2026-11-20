var PutIODownloader = new Class({

	initialize: function(){
		var self = this;

		App.addEvent('loadSettings', self.addRegisterButton.bind(self));
	},

	addRegisterButton: function(){
		var self = this;

		var setting_page = App.getPage('Settings');
		setting_page.addEvent('create', function(){

		 	var fieldset = setting_page.tabs.downloaders.groups.putio,
		 		l = window.location;

			var putio_set = 0;
		 	fieldset.getElements('input[type=text]').each(function(el){
		 		putio_set += +(el.get('value') !== '');
		 	});

			new Element('.ctrlHolder').adopt(

			 	// Unregister button
			 	(putio_set > 0) ?
			 		[
						self.unregister = new Element('a.button.red', {
							'text': 'Unregister',
							'events': {
								'click': function(){
									fieldset.getElements('input[name*=oauth_token]').set('value', '').fireEvent('change');

									self.unregister.destroy();
									self.unregister_or.destroy();
								}
							}
						}),
						self.unregister_or = new Element('span[text=or]')
					]
			 	: null,

				// Register button: link with a code entered at put.io/link, shown right here
				new Element('a.button', {
					'text': putio_set > 0 ? 'Register a different account' : 'Register your put.io account',
					'events': {
						'click': function(){
							self.startSignIn();
						}
					}
				}),

				self.sign_in_status = new Element('div.putio_sign_in', {'styles': {'margin-top': 10}})
			).inject(fieldset.getElement('.test_button'), 'before');
		});

	},

	startSignIn: function(){
		var self = this;

		clearTimeout(self.poll_timer);
		self.sign_in_status.set('text', 'Asking put.io for a code...');

		Api.request('downloader.putio.device_code', {
			'onComplete': function(json){
				if(!json || !json.success){
					self.sign_in_status.set('text', 'Could not start linking: ' + ((json && json.error) || 'no answer'));
					return;
				}

				self.sign_in_status.empty().adopt(
					new Element('span', {'text': 'Go to '}),
					new Element('a', {
						'href': json.verification_url,
						'target': '_blank',
						'text': json.verification_url
					}),
					new Element('span', {'text': ' and enter this code: '}),
					new Element('strong', {
						'text': json.user_code,
						'styles': {'font-size': '1.4em', 'letter-spacing': '0.1em'}
					}),
					self.poll_state = new Element('div', {'text': 'Waiting for you to enter it...'})
				);

				self.poll(json.interval * 1000);
			}
		});
	},

	poll: function(interval){
		var self = this;

		self.poll_timer = setTimeout(function(){
			Api.request('downloader.putio.device_poll', {
				'onComplete': function(json){
					var status = json && json.status;

					if(status == 'connected'){
						self.sign_in_status.set('text', 'Linked to put.io. Reloading settings...');
						setTimeout(function(){ window.location.reload(); }, 1500);
					}
					else if(status == 'pending')
						self.poll(interval);
					else
						self.poll_state.set('text', (status == 'expired' ? 'The code expired before it was entered.' : 'Linking did not work (' + (status || 'no answer') + ').') + ' Click the button to try again.');
				}
			});
		}, interval);
	}

});

window.addEvent('domready', function(){
	new PutIODownloader();
});
