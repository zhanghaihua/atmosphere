/* base.js
 * Backbone.js base model functionality.
 */
define(['backbone'], function(Backbone) {

    var Base = Backbone.Model.extend({
        defaults: {
            'model_name': 'base'
        },
        urlRoot: '/api/v1',
        url: function() {
            if (!this.identity)
                console.error("Model must be instantiated with identity option");
            var creds = {
                provider_id: this.identity.get('provider_id'),
                identity_id: this.identity.id
            };
            var url = this.urlRoot
                + '/provider/' + creds.provider_id
                + '/identity/' + creds.identity_id
                + '/' + this.defaults.model_name + '/';
            
            if (this.get('id') !== undefined) {
                url += this.get('id') + '/';
            }

            return url;
        }
    });

    return Base;

});
