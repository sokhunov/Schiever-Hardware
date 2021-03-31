from flask import Flask, render_template, request, redirect, url_for, flash
import modules.model as model
import secrets

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

secret = secrets.token_urlsafe(32)
app.secret_key = secret

@app.route('/')
def hardware_list():
    list_of_hardware = model.Hardware.get_list_of_hardware()
    return render_template('hardwareList.html', list_of_hardware=list_of_hardware)


@app.route('/prepare_for_arrange', methods=['POST'])
def prepare_for_arrange():
    data = request.form.to_dict(flat=False)
    if not data:
        print('No data')
        redirect(url_for('hardware_list'))
    else:
        selected_hardware = data['hardware_id']
        arrange_params = model.PreArrange(hardware=selected_hardware)
        return render_template('arrange_hardware.html', arrange_params=arrange_params)


@app.route('/arrange_hardware', methods=['POST'])
def arrange_hardware():
    form_data = request.form.to_dict(flat=False)
    result = model.ArrangeHardware(**form_data)
    message, status = result.arrange()
    flash(message, status)
    return redirect(url_for('hardware_list'))
