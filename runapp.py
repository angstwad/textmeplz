# -*- coding: utf-8 -*-

from textmeplz.app import create_app


def main():
    app_dct = create_app()
    app = app_dct['flask']
    app.before_first_request_funcs = []
    app.run(debug=True)

if __name__ == '__main__':
    main()
