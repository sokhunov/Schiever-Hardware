from flask import Flask, render_template, request, redirect, url_for, flash
import modules.model as model
import secrets
import pdfkit

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
    # pdfkit.from_file('./templates/arrange_hardware.html', r'd:\TEST.pdf')
    form_data = request.form.to_dict(flat=False)
    arrange_ins = model.ArrangeHardware(**form_data)
    message, status = arrange_ins()
    flash(message, status)
    return redirect(url_for('hardware_list'))


@app.route('/edit_hardware/<hardware_id>', methods=['GET'])
def pre_edit_hardware(hardware_id):
    hardware_info = model.HardwareEdit(hardware_id=hardware_id)
    hardware_info()
    return render_template('edit_hardware.html', hardware_info=hardware_info)


@app.route('/edit_hardware', methods=['POST'])
def edit_hardware():
    form_data = request.form.to_dict()
    hardware_to_edit = model.Hardware(**form_data)
    hardware_to_edit.edit_hardware()
    return redirect(url_for('hardware_list'))


@app.route('/arrange_info/<hardware_id>')
def arrangement_info(hardware_id):
    hardware_arran_history = model.ArrangeHardware.get_hardware_arrangement(hardware_id=hardware_id)
    print(hardware_arran_history)
    return redirect(url_for('hardware_list'))
