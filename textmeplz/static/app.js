(function () {
    angular.module('textmeplz.config', ['angularPayments', 'angularSpinner', 'oitozero.ngSweetAlert'])
        .constant('appConfig', {
            backend: window.location.origin + '/api'
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
        window.Stripe.setPublishableKey('pk_live_Q9LQQ3UXnLwAvxsnwHNsMhgJ');
    });


    app.controller('accountController', [
        '$http', 'appConfig',
        function ($http, appConfig) {
            var self = this,
                accountActivateUrl = appConfig.backend + '/user/activate',
                phoneNumberUrl = appConfig.backend + '/user/phone',
                resetAccountUrl = appConfig.backend + '/user/reset';

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
                        alert('There was a problem loading account activation data.');
                    }
                )
            }

            this.activate = function () {
                $http.post(accountActivateUrl).then(
                    getActive,
                    function () {
                        alert('Failed to activate account.');
                    }
                )
            };

            this.deactivate = function () {
                $http.delete(accountActivateUrl).then(
                    getActive,
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
                    getUser,
                    function () {
                        alert('Error deleting phone number');
                    }
                )
            };

            this.resetAccount = function () {
                self.resetting = true;
                $http.post(resetAccountUrl).then(
                    function () {
                        getUser();
                        getActive();
                        self.resetting = false;
                        alert('Your account has been reset.');
                    },
                    function () {
                        self.resetting = false;
                        alert('There was a problem resetting your account.');
                    }
                )
            }

        }
    ]);


    app.controller('rechargeController', [
        '$q',
        '$http',
        '$scope',
        '$location',
        'appConfig',
        'SweetAlert',
        function ($q, $http, $scope, $location, appConfig, SweetAlert) {
            var self = this;

            $scope.amount = 10;

            this.prices = [5, 10, 20, 50, 100];
            this.priceMap = {
                5: 165,
                10: 342,
                20: 695,
                50: 1754,
                100: 3520
            };

            function chargeCard(card) {
                var deferred = $q.defer();
                var data = {
                    amount: $scope.amount,
                    card: card
                };
                $http.post(appConfig.backend + '/payment/process', data).then(
                    function (response) {
                        deferred.resolve(response.data);
                    },
                    function (response) {
                        deferred.reject(response);
                    }
                );
                return deferred.promise;
            }

            $scope.onSubmit = function () {
                $scope.processing = true;
            };

            $scope.stripeCallback = function (status, response) {
                if (status == 402) {
                    $scope.processing = false;
                    SweetAlert.swal({
                        title: 'There was a problem processing payment!',
                        text: response.error.message,
                        type: 'error'
                    });
                }
                else if (status != 200) {
                    $scope.processing = false;
                    SweetAlert.swal({
                        title: 'There was a problem processing payment!',
                        text: 'An unknown error occurred.  Your card was not charged.',
                        type: 'error'
                    });
                }
                else {
                    var promise = chargeCard(response);
                    promise.then(
                        function (data) {
                            SweetAlert.swal({
                                title: 'Complete!',
                                text: 'Your account has been successfully recharged.',
                                type: 'success',
                                timeout: 3000
                            }, function () {
                                $location.url('/account');
                            });
                        },
                        function (response) {
                            SweetAlert.swal({
                                title: 'There was a problem processing payment!',
                                text: 'An unknown error occurred.  Your card was not charged.',
                                type: 'error'
                            }, function () {
                                $location.url('/account');
                            });
                        }
                    );
                    promise.finally(function () {
                        $scope.processing = false;
                    });
                }
            };

        }
    ]);


})();
