from modules.hardware import Hardware
from flask import Flask, render_template, request, redirect, url_for
from modules.arranges import PreArrange, arrange

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


@app.route('/')
def hardware_list():
    list_of_hardware = Hardware.get_list_of_hardware()
    return render_template('hardwareList.html', list_of_hardware=list_of_hardware)


@app.route('/prepare_for_arrange', methods=['POST'])
def prepare_for_arrange():
    data = request.form.to_dict(flat=False)
    if not data:
        print('No data')
        redirect(url_for('hardware_list'))
    else:
        selected_hardware = data['hardware_id']
        arrange_params = PreArrange(hardware=selected_hardware)
        return render_template('arrange_hardware.html', arrange_params=arrange_params)


@app.route('/arrange_hardware', methods=['POST'])
def arrange_hardware():
    form_data = request.form.to_dict(flat=False)
    print(form_data)