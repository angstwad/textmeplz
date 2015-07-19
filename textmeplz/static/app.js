(function () {
    angular.module('textmeplz.config', ['angularPayments', 'oitozero.ngSweetAlert'])
        .constant('appConfig', {
            backend: 'http://127.0.0.1:5000/api'
        });

    var app = angular.module('textmeplz.app', [
        'ngRoute',
        'ui.bootstrap',
        'textmeplz.config'
    ]);

    app.filter('titlecase', function () {
        return function (s) {
            s = ( s === undefined || s === null ) ? '' : s;
            return s.toString().toLowerCase().replace(/\b([a-z])/g, function (ch) {
                return ch.toUpperCase();
            });
        };
    });


    app.config(function ($routeProvider) {
        $routeProvider
            .when('/account', {
                templateUrl: 'static/account.html',
                controller: 'accountController',
                controllerAs: 'acctCtrl'
            })
            .when('/account/recharge', {
                templateUrl: 'static/recharge.html',
                controller: 'rechargeController',
                controllerAs: 'recharge'
            })
            .otherwise('/account');
        window.Stripe.setPublishableKey('pk_test_rOeDMssmkV4UlUTAcVYBZYSy');
    });


    app.controller('accountController', [
        '$http', 'appConfig',
        function ($http, appConfig) {
            var self = this;
            var accountActivateUrl = appConfig.backend + '/user/activate';
            var phoneNumberUrl = appConfig.backend + '/user/phone';

            getUser();
            getActive();

            function getUser() {
                var getUserUrl = appConfig.backend + '/user';
                $http.get(getUserUrl).then(
                    function (response) {
                        self.data = response.data;
                    },
                    function () {
                        alert('There was a problem loading account data.');
                    }
                );
            }

            function getActive() {
                $http.get(accountActivateUrl).then(
                    function (response) {
                        self.isActive = response.data.active;
                    },
                    function () {
                        console.log(arguments);
                        alert('There was a problem loading account activation data.');
                    }
                )
            }

            this.activate = function () {
                $http.post(accountActivateUrl).then(
                    getActive(),
                    function () {
                        alert('Failed to activate account.');
                    }
                )
            };

            this.deactivate = function () {
                $http.delete(accountActivateUrl).then(
                    getActive(),
                    function () {
                        alert('Failed to deactivate account.');
                    }
                )
            };

            this.addNumber = function () {
                var data = {number: self.phoneNumberInput};
                $http.post(phoneNumberUrl, data).then(
                    function () {
                        self.phoneNumberInput = null;
                        getUser();
                    },
                    function () {
                        alert('Error adding phone number');
                    }
                )
            };

            this.deleteNumber = function (number) {
                var config = {
                    data: {
                        number: number
                    },
                    headers: {
                        'Content-Type': 'application/json',
                    }
                };
                $http.delete(phoneNumberUrl, config).then(
                    getUser(),
                    function () {
                        alert('Error deleting phone number');
                    }
                )
            };

        }
    ]);


    app.controller('rechargeController', [
        '$scope',
        'SweetAlert',
        function ($scope, SweetAlert) {
            var self = this;

            $scope.amount = 10;

            this.prices = [5, 10, 20, 50, 100];
            this.priceMap = {
                5: 125,
                10: 275,
                20: 600,
                50: 1600,
                100: 3400
            };
            this.months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'];

            this.getYears = function(){
                var startYear = new Date().getFullYear(),
                    endYear = startYear + 5,
                    years = [];
                while ( startYear <= endYear ) { years.push(startYear++); }
                return years;
            };

            function sendPaymentBack(paymentObj){

            }

            $scope.stripeCallback = function(status, response){
                if (status != 200){

                } else {

                }
            };
        }
    ]);
})();
