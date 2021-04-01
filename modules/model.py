from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func
from datetime import datetime, date
from modules.session_manager import load_session


Base = automap_base()

# === Arrange


class ArrangeOperation(Base):
    """
    Arrange operations types:
        1 = Принял(а)
        2 = Сдал(а)
        3 = Передал(а)
    """

    ACCEPT = 1  # Принял(а)
    RETURN = 2  # Сдал(а)
    TRANSFER = 3  # Передал(а)

    __tablename__ = 'arrange_operations'

    operation_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))

    def __repr__(self):
        return f'ArrangeOperation(id={self.operation_id}, name={self.name})'


class ArrangeStatus(Base):
    """
    Hardware arrange statuses:
        1 = Свободен
        2 = Используется
    """
    FREE = 1
    IN_USE = 2

    __tablename__ = 'arrange_statuses'

    arr_status_id = Column(Integer, primary_key=True)
    name = Column(String(50))

    def __repr__(self):
        return f'ArrangeStatus(id={self.arr_status_id}, name={self.name})'


class ArrangeHardware(Base):

    STATUS_MESSAGES = {
        0: {'message': 'Done.', 'status': 'bg-success'},
        1: {'message': 'Hardware {} is in use', 'status': 'bg-danger'},
        2: {'message': 'Hardware {} belong to another worker', 'status': 'bg-danger'},

    }

    __tablename__ = 'arranges'

    arrange_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    hardware_id = Column(Integer, ForeignKey('hardware.hardware_id'))
    employee_id = Column(Integer, ForeignKey('workers.worker_id'))
    it_worker_id = Column(Integer, ForeignKey('workers.worker_id'))
    employee2_id = Column(Integer, ForeignKey('workers.worker_id'), nullable=True)
    operation_id = Column(Integer, ForeignKey('arrange_operations.operation_id'))
    doc_num = Column(Integer)  # Act number
    doc_date = Column(Date, default=date.today)
    log_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # -- relationships
    hardware = relationship('Hardware', viewonly=True)
    employee = relationship('Worker', foreign_keys=[employee_id])
    employee2 = relationship('Worker', foreign_keys=[employee2_id])
    operation = relationship('ArrangeOperation', backref='arranges')
    it_worker = relationship('Worker', foreign_keys=[it_worker_id])

    def __init__(self, **kwargs):
        self.hardware_id = [int(h_id) for h_id in kwargs['hardware_id']]
        self.it_worker_id = int(kwargs['it_worker'][0])
        self.employee_id = int(kwargs['employee'][0])
        self.operation_id = int(kwargs['operation'][0])
        self.doc_num = kwargs['doc_num'][0]
        self.doc_date = kwargs['doc_date'][0]
        self.employee2_id = int(kwargs['employee_2'][0]) if kwargs['employee_2'][0] else None
        self.db_session = load_session()
        self.hardware_arrange = self.get_hardware()
        self.unavailable_hardware = []

        self.create_hardware_for_arrange()

    def __repr__(self):
        return f'Arrange(hardware = {self.hardware}, it_worker_id = {self.it_worker}, employee = {self.employee}' \
               f'operation = {self.operation} '

    @hybrid_method
    def get_hardware(self) -> list:
        result = self.db_session.query(Hardware).filter(Hardware.hardware_id.in_(self.hardware_id)).all()
        return result

    def arrange(self):
        status_code = self.validate_operation()
        if status_code != 0:
            return self.get_status_message(status_code)

        self.arrange_to_employee()

        return self.get_status_message(status_code)

    @hybrid_method
    def get_status_message(self, status_code=0):
        if status_code == 0:
            return self.STATUS_MESSAGES[status_code]['message'],\
                   self.STATUS_MESSAGES[status_code]['status']
        else:
            return self.STATUS_MESSAGES[status_code]['message'].format(self.unavailable_hardware), \
                   self.STATUS_MESSAGES[status_code]['status']

    @hybrid_method
    def create_hardware_for_arrange(self):
        """
        Create hardware which is not in the db table Hardware_use
        :return:
        """
        for hardware_ in self.hardware_arrange:
            if not hardware_.hardware_use:
                new_hdw = HardwareUse(hardware_id=hardware_.hardware_id)
                hardware_.hardware_use = new_hdw

        self.db_session.commit()

    @hybrid_method
    def validate_operation(self):
        status = 0
        # Employee "Принял" in this case we check if all hardware in status "Свободен"
        if self.operation_id == ArrangeOperation.ACCEPT:
            self.unavailable_hardware = self.check_hardware_use_status()
            if self.unavailable_hardware:
                status = 1
        # Employee "Сдал" или "Передал" in this case we check is the worker is the owner
        elif self.operation_id in [ArrangeOperation.RETURN, ArrangeOperation.TRANSFER]:
            self.unavailable_hardware = self.check_hardware_owner()
            if self.unavailable_hardware:
                status = 2

        return status

    @hybrid_method
    def check_hardware_use_status(self) -> list:
        """
        Get list of hardware which in arrange status == "in use"
        :return:
        """
        return [hardware for hardware in self.hardware_arrange if hardware.hardware_use.status_id == 2]

    @hybrid_method
    def check_hardware_owner(self) -> list:
        """
        Get list of hardware which is not belong to the employee
        :return:
        """
        return [hardware for hardware in self.hardware_arrange if hardware.hardware_use.employee_id != self.employee_id]

    @hybrid_method
    def arrange_to_employee(self):
        """
        If operation == RETURN then change status of all hardware to FREE
        elif operation == ACCEPT then change status and owner to employee
        elif operation == TRANSFER then change status and owner to employee2
        :return:
        """
        if self.operation_id == ArrangeOperation.RETURN:  # Сдал
            self.proceed_arrange(status_id=ArrangeStatus.FREE)
        elif self.operation_id == ArrangeOperation.ACCEPT:
            self.proceed_arrange(status_id=ArrangeStatus.IN_USE, employee_id=self.employee_id)
        elif self.operation_id == ArrangeOperation.TRANSFER:
            self.proceed_arrange(status_id=ArrangeStatus.IN_USE, employee_id=self.employee2_id)

    @hybrid_method
    def proceed_arrange(self, status_id, employee_id=None):
        for hardware_ in self.hardware_arrange:
            hardware_.hardware_use.doc_date = self.doc_date
            hardware_.hardware_use.doc_num = self.doc_num
            hardware_.hardware_use.status_id = status_id
            hardware_.hardware_use.employee_id = employee_id

        self.db_session.commit()


class PreArrange:
    def __init__(self, hardware):
        self.db_session = load_session()
        self.hardware = self.get_selected_hardware(hardware_id=hardware)
        self.it_workers = self.get_workers(it_workers=True)
        self.workers = self.get_workers(it_workers=False)
        self.doc_num = self.get_next_doc_num()
        self.arrange_operations = self.get_arrange_operations()
        self.doc_date = date.today()

    def get_workers(self, it_workers: bool) -> list:
        """
        Get all rows from workers DB table with department id == 1 (i.e IT workers)
        :param it_workers: <bool> if True: return it workers else return all except it workers
        :return -> list: List of it workers
        """
        if it_workers:
            return self.db_session.query(Worker).filter(Worker.department_id == 1).all()
        else:
            return self.db_session.query(Worker).filter(Worker.department_id != 1).all()

    def get_next_doc_num(self):
        """
        Get the last document number from DB table HardwareUse
        :return:
        """
        last_doc_num = self.db_session.query(func.max(HardwareUse.doc_num)).scalar()
        if not last_doc_num:
            return 1

        return last_doc_num + 1

    def get_arrange_operations(self):
        return self.db_session.query(ArrangeOperation).all()

    def get_selected_hardware(self, hardware_id: list):
        return self.db_session.query(Hardware).filter(Hardware.hardware_id.in_(hardware_id)).all()


# === Hardware

class Brand(Base):
    """
    Hardware brands (e.g HP, Dell etc..)
    """

    __tablename__ = 'brands'

    brand_id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'Brand(condition_id = {self.brand_id}, name = {self.name})'


class HardwareCondition(Base):
    """
    Hardware conditions (e.g new, undefined and etc ..)
    """
    __tablename__ = 'hardware_conditions'

    condition_id = Column(Integer, primary_key=True)
    name = Column(String)

    def __repr__(self):
        return f'HardwareCondition(condition_id = {self.condition_id}, name = {self.name})'


class HardwareType(Base):
    """
    Hardware types (e.g laptop, phone, PC and etc ..)
    """
    __tablename__ = 'hardware_types'

    type_id = Column(Integer, primary_key=True)
    name = Column(String)


class Hardware(Base):
    __tablename__ = 'hardware'
    __table_args__ = {'extend_existing': True}

    # -- DB table columns
    hardware_id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String)
    hardware_condition_id = Column('id_condition', Integer, ForeignKey('hardware_conditions.condition_id'))
    hardware_type_id = Column('id_type', Integer, ForeignKey('hardware_types.type_id'))
    hardware_brand_id = Column('id_brand', Integer, ForeignKey('brands.brand_id'))
    serial_num = Column(String, nullable=True)
    description = Column('descrip', String, nullable=True)
    validation_date = Column(Date, default=date.today)
    log_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    # -- relationships
    hardware_brand = relationship('Brand', viewonly='True')
    hardware_condition = relationship('HardwareCondition', viewonly='True')
    hardware_type = relationship('HardwareType', viewonly='True')
    hardware_use = relationship('HardwareUse', backref='hardware_use', uselist=False)

    def __init__(self, **hardware_data):
        self.hardware_id = int(hardware_data['hardware_id'])
        self.name = hardware_data['hardware_name']
        self.hardware_condition_id = hardware_data['condition_id']
        self.hardware_type_id = int(hardware_data['type_id'])
        self.hardware_brand_id = int(hardware_data['brand_id'])
        self.validation_date = hardware_data['validation_date']
        self.serial_num = hardware_data.get('serial', None)
        self.description = hardware_data.get('description', None)

    def __repr__(self):
        return f'Hardware(hardware_id={self.hardware_id}, name={self.name}'

    @hybrid_method
    def get_list_of_hardware(self):
        db_session = load_session()
        result = db_session.query(Hardware).all()
        return result

    @classmethod
    def get_hardware(cls, hardware_id):
        db_session = load_session()
        hrdw = db_session.query(Hardware).filter(Hardware.hardware_id == hardware_id).scalar()
        db_session.close()
        return hrdw

    @hybrid_property
    def code_format(self):
        return str(self.hardware_id).zfill(8)

    @hybrid_method
    def edit_hardware(self):
        db_session = load_session()
        hardware = db_session.query(Hardware).filter(Hardware.hardware_id == self.hardware_id).scalar()

        hardware.name = self.name
        hardware.hardware_condition_id = self.hardware_condition_id
        hardware.hardware_type_id = self.hardware_type_id
        hardware.hardware_brand_id = self.hardware_brand_id
        hardware.validation_date = self.validation_date
        hardware.serial_num = self.serial_num
        hardware.description = self.description
        db_session.commit()
        db_session.close()


class HardwareEdit:
    def __init__(self, hardware_id):
        self.hardware_id = hardware_id

    def __call__(self):
        db_session = load_session()
        self.hardware = db_session.query(Hardware).filter(Hardware.hardware_id == self.hardware_id).scalar()
        self.hardware_conditions = db_session.query(HardwareCondition).all()
        self.hardware_types = db_session.query(HardwareType).all()
        self.hardware_brands = db_session.query(Brand).all()
        db_session.close()

# === Hardware Use


class HardwareUse(Base):
    """

    Таблица БД в которой хранится ПОСЛЕДНЯЯ информация о оборудованиях.
    Из этой таблицы можно получить информации:
    Доступно ли оборудование, на чье имя оборудование, номер акта, дата акта

    """

    __tablename__ = 'hardware_use'

    hardware_id = Column(Integer, ForeignKey('hardware.hardware_id'), primary_key=True, unique=True)
    employee_id = Column(Integer, ForeignKey('workers.worker_id'), nullable=True)
    status_id = Column(Integer, ForeignKey('arrange_statuses.arr_status_id'), default=ArrangeStatus.FREE)
    doc_num = Column(Integer, nullable=True)
    doc_date = Column(Date, default=date.today)
    log_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    status = relationship('ArrangeStatus', viewonly=True)
    employee = relationship('Worker', viewonly=True)

    def __repr__(self):
        return f'{self.hardware_id}-{self.hardware.name}, status {self.status.name}'

    def status_color(self):
        if self.status_id == ArrangeStatus.FREE:
            return 'bg-success'
        elif self.status_id == ArrangeStatus.IN_USE:
            return 'bg-hardware-unavailable'


# === Worker


class Department(Base):
    """
    Workers departments (e.g HR, IT and etc..)
    """

    __tablename__ = 'departments'

    department_id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(50))

    def __init__(self, dept_id, name):
        self.department_id = dept_id
        self.name = name


class Worker(Base):
    """
    Workers table with name, workers id (tabelniy nomer), department info
    """

    __tablename__ = 'workers'

    worker_id = Column(Integer, primary_key=True, autoincrement=False)  # tabelniy nomer
    name = Column(String(50))
    department_id = Column(Integer, ForeignKey('departments.department_id'))

    department = relationship('Department', viewonly=True)
    worker_hardware = relationship('HardwareUse', backref='workers')

    def __init__(self, worker_id, name, department_id):
        self.worker_id = worker_id
        self.name = name
        self.department_id = department_id


Base.prepare()
