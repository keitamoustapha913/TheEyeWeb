from flask_server import db ,bcrypt

from flask_admin import AdminIndexView
from flask import url_for, redirect, render_template, request, abort, make_response, jsonify

import flask_login as login

from flask_admin import helpers, expose, expose_plugview
from flask_server.home_index.auth_model import User
from flask_server.home_index.auth_forms import LoginForm, RegistrationForm



# Create customized index view class that handles login & registration
class MyAdminIndexView(AdminIndexView):

    @expose('/')
    def index(self):
        """
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        """
        
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            print(f' \n Validating ... ')
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            print(f' \n Authenticated User {login.current_user}')
            return redirect(url_for('.index'))
        
        next_page = request.args.get('next')
        print("\n\n\n next_page : ",next_page )
        link = '<p>Don\'t have an account? <a href="' + url_for('.register_view') + '">Click here to register.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        self._template_args['auth_title'] = "Login"
        return self.render('admin/authentication/login.html')

    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):
        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        form = RegistrationForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = User()

            form.populate_obj(user)
            # we hash the users password to avoid saving it as plaintext in the db,
            # remove to use plain text:
            user.password = bcrypt.generate_password_hash(form.password.data)

            db.session.add(user)
            db.session.commit()

            login.login_user(user)
            return redirect(url_for('.index'))
        link = '<p>Already have an account? <a href="' + url_for('.login_view') + '">Click here to log in.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        self._template_args['auth_title'] = "Register"
        return self.render('admin/authentication/register.html')

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        self._template_args['auth_title'] = "Logout"
        return redirect(url_for('.index'))

