# -*- coding: utf-8 -*-

from textmeplz.apps import create_app


def main():
    app_dct = create_app()
    app_dct['flask'].run(debug=True)

if __name__ == '__main__':
    main()
