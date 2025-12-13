import os
from flask import Flask, redirect, url_for, request, render_template, flash, g, session

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    app.add_url_rule('/auth', endpoint='index')

    # register blueprint "calendar"
    from . import calendar
    app.register_blueprint(calendar.bp)
    app.add_url_rule('/calendar', endpoint='show_cal')

    # register blueprint "activity"
    from . import activity
    app.register_blueprint(activity.bp)
    app.add_url_rule('/activity', endpoint='index')

    # register blueprint "team"
    from . import team
    app.register_blueprint(team.bp)
    app.add_url_rule('/team', endpoint='index')

    # register blueprint "home"
    from . import home
    app.register_blueprint(home.bp)
    app.add_url_rule('/home', endpoint='index')

    @app.route('/fc_sync')
    def fc_call_1():
       session["fc_call_type"] = "fc_sync"
       print("fc_call_1")
       print(session["fc_call_type"])
       return redirect('/oauth')
      
    from . import fcsync
    @app.route('/oauth')
    def get_token():
        print('session["fc_call_type"] da /oauth: ' + session["fc_call_type"])
        if g.role != "ADMIN":
         error = 'Non sei autorizzato a questa funzione.'
         flash(error)
         return redirect(url_for("calendar.show_cal"))
        fcsync_ist = fcsync.Oauth()
        fc_url = fcsync_ist.get_oauth_access_token()
        #print("fc_url: " + fc_url)
        return redirect(fc_url)
    
# register blueprint "site"
    from . import site
    app.register_blueprint(site.bp)
    app.add_url_rule('/site', endpoint='index')

# register blueprint "order"
    from . import order
    app.register_blueprint(order.bp)
    app.add_url_rule('/order', endpoint='index')

# register blueprint "customer"
    from . import customer
    app.register_blueprint(customer.bp)
    app.add_url_rule('/customer', endpoint='index')

# register blueprint "timesheet"
    from . import timesheet
    app.register_blueprint(timesheet.bp)
    app.add_url_rule('/timesheet', endpoint='index')

# register blueprint "view_people_timesheet"
    from . import view_people_timesheet
    app.register_blueprint(view_people_timesheet.bp)
    app.add_url_rule('/view_people_timesheet', endpoint='index')

# register blueprint "tool_usage"
    from . import tool_usage
    app.register_blueprint(tool_usage.bp)
    app.add_url_rule('/tool_usage', endpoint='index')

# register blueprint "accounting_hours"
    from . import accounting_hours
    app.register_blueprint(accounting_hours.bp)
    app.add_url_rule('/accounting_hours', endpoint='index')

# register blueprint "export_timesheet"
    from . import export_timesheet
    app.register_blueprint(export_timesheet.bp)
    app.add_url_rule('/export_timesheet', endpoint='index')

# register blueprint "maintenance"
    from . import maintenance
    app.register_blueprint(maintenance.bp)
    app.add_url_rule('/maintenance', endpoint='index')

# register blueprint "calendar_maint"
    from . import cal_maintenance
    app.register_blueprint(cal_maintenance.bp)
    app.add_url_rule('/cal_maintenance', endpoint='show_cal')

# register blueprint "schedule"
    from . import schedule
    app.register_blueprint(schedule.bp)
    app.add_url_rule('/schedule', endpoint='index')


# register blueprint "cal_schedule"
    from . import cal_schedule
    app.register_blueprint(cal_schedule.bp)
    app.add_url_rule('/cal_schedule', endpoint='show_cal')

# register blueprint "cal_holidays"
    from . import cal_holidays
    app.register_blueprint(cal_holidays.bp)
    app.add_url_rule('/cal_holidays', endpoint='show_cal')

# register blueprint "cal_order"
    from . import cal_order
    app.register_blueprint(cal_order.bp)
    app.add_url_rule('/cal_order', endpoint='cal')

# register blueprint "cal_team_planned"
    from . import cal_team_planned
    app.register_blueprint(cal_team_planned.bp)
    app.add_url_rule('/cal_team_planned', endpoint='show_cal')

# register blueprint "tool"
    from . import tool
    app.register_blueprint(tool.bp)
    app.add_url_rule('/tool', endpoint='index')

# register blueprint "people"
    from . import people
    app.register_blueprint(people.bp)
    app.add_url_rule('/people', endpoint='index')

# register blueprint "people_payment"
    from . import people_payment
    app.register_blueprint(people_payment.bp)
    app.add_url_rule('/people_payment', endpoint='index')

# register blueprint "people_available"
    from . import people_available
    app.register_blueprint(people_available.bp)
    app.add_url_rule('/people_available', endpoint='index')

# register blueprint "cal_availability"
    from . import cal_availability
    app.register_blueprint(cal_availability.bp)
    app.add_url_rule('/cal_availability', endpoint='show_cal')

# register blueprint "cal_order_invoice"
    from . import cal_order_invoice
    app.register_blueprint(cal_order_invoice.bp)
    app.add_url_rule('/cal_order_invoice', endpoint='show_cal')

# register blueprint "rentry"
    from . import rentri
    app.register_blueprint(rentri.bp)
    app.add_url_rule('/rentri', endpoint='index')

    return app

