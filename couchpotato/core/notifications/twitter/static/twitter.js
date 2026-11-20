var TwitterNotification = new Class({

	initialize: function(){
		var self = this;
		App.addEvent('loadSettings', self.addRegisterButton.bind(self));
	},

	// Optional: sign in through X instead of pasting the access token. Needs the app's API key +
	// secret filled in, and this install's callback URL on the app's list at developer.x.com.
	addRegisterButton: function(){
		var self = this;

		var setting_page = App.getPage('Settings');
		setting_page.addEvent('create', function(){

			var fieldset = setting_page.tabs.notifications.groups.twitter,
				l = window.location,
				account = fieldset.getElements('input[name*=access_token], input[name*=screen_name]'),
				screen_name = fieldset.getElement('input[name*=screen_name]'),
				signed_in = fieldset.getElement('input[name*=access_token_key]').get('value') !== '';

			new Element('.ctrlHolder').adopt(

				// Forget the account (keeps the app's API key + secret)
				signed_in ?
					[
						self.unregister = new Element('a.button.red', {
							'text': 'Sign out' + (screen_name && screen_name.get('value') ? ' "' + screen_name.get('value') + '"' : ''),
							'events': {
								'click': function(){
									account.set('value', '').fireEvent('change');

									self.unregister.destroy();
									self.unregister_or.destroy();
								}
							}
						}),
						self.unregister_or = new Element('span[text=or]')
					]
				: null,

				new Element('a.button', {
					'text': signed_in ? 'Sign in to a different X account' : 'Sign in with X (instead of pasting the access token)',
					'events': {
						'click': function(){
							Api.request('notify.twitter.auth_url', {
								'data': {
									'host': l.protocol + '//' + l.hostname + (l.port ? ':' + l.port : '')
								},
								'onComplete': function(json){
									if(json && json.success && json.url)
										window.location = json.url;
									else
										alert((json && json.error) || 'X refused the sign-in. Check the log for why.');
								}
							});
						}
					}
				})
			).inject(fieldset.getElement('.test_button'), 'before');
		});

	}

});

window.addEvent('domready', function(){
	new TwitterNotification();
});
