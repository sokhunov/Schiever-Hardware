from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from datetime import date, datetime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_method
from modules.workers import Worker

Base = automap_base()


class Brand(Base):
    """
    Hardware brands (e.g HP, Dell etc..)
    """
    __tablename__ = 'brands'

    brand_id = Column(Integer, primary_key=True)
    name = Column(String)


class HardwareCondition(Base):
    """
    Hardware conditions (e.g new, undefined and etc ..)
    """
    __tablename__ = 'hardware_conditions'

    condition_id = Column(Integer, primary_key=True)
    name = Column(String)


class HardwareType(Base):
    """
    Hardware types (e.g laptop, phone, PC and etc ..)
    """
    __tablename__ = 'hardware_types'

    type_id = Column(Integer, primary_key=True)
    name = Column(String)


class HardwareUse(Base):
    """
    Contains information about current statuses of the hardware:
    Whether hardware is free or in use, who is the owner, who arranged the hardware, doc num and doc date
    """

    __tablename__ = 'hardware_use'

    hardware_id = Column(primary_key=True, unique=True)
    employee_id = Column(Integer, ForeignKey('workers.worker_id'), nullable=True)
    status_id = Column(Integer, ForeignKey('arrange_statuses.arr_status_id'))
    doc_num = Column(Integer, nullable=True)
    doc_date = Column(Date, default=date.today)

    status = relationship(ArrangeStatus)
    employee = relationship(Worker)

    def __init__(self, hardware_id, session=None, employee_id=None, status_id=None, doc_num=None, doc_date=None):
        self.hardware_id = hardware_id
        self.session = session
        self.employee_id = employee_id
        self.status_id = status_id
        self.doc_num = doc_num
        self.doc_date = doc_date

    def __repr__(self):
        return f'{self.hardware_id} {self.status.name} {self.employee.name}'

    @hybrid_method
    def get_missing_hardware(self):
        """
        Проверим существуют ли все выбранные оборудования в БД таблице Hardware_use и возвратим отсутствующие оборудов.
        :return hardware_not_exist: -> list(). Список выбранныъ кодов отсутствующих в таблице Hardware_use
        """
        missing_hardware = []
        result = self.session.query(HardwareUse.hardware_id).filter(HardwareUse.hardware_id.in_(self.hardware_id)).all()
        if result:
            hardware_list = list(map(lambda x: x[0], result))  # convert from [(id1, ), (id2,) ..] to list [id1, id2 ..]
            # hardware which is not in the result list
            missing_hardware = [hd for hd in self.hardware_id if hd not in hardware_list]
        if not result:
            missing_hardware.extend(self.hardware_id)

        return missing_hardware

    @hybrid_method
    def create_hardware(self, hardware_list):
        """
        Создаем записи оборудований в БД Hardware_use
        :param hardware_list: Список кодов оборудований для создания
        :return:
        """
        hardware_to_create = []
        for hdw_id in hardware_list:
            new_hardware = HardwareUse(hardware_id=hdw_id, status_id=1)  # status_id = "Свободен" по умолч.
            hardware_to_create.append(new_hardware)

        self.session.add_all(hardware_to_create)
        self.session.commit()

    @hybrid_method
    def check_availability(self, operation_id):
        """
        Проверим доступность оборудований.
        Если operation_id == 1, значит сотрудник получает оборудование(я) и статус у этих оборудований должен быть
        1 (Свободен)

        Если operation_id 2(Сдал) или 3(Передал), значит сотрудник сдает оборудование(я) и они должны быть оформлены на
        его имя.

        :param operation_id: Код Операции оформления
        :return unavailable_hardware: -> list(). Список недоступных оборудований.
        """
        unavailable_hardware = []
        if operation_id == 1:  # Employee "Принял" in this case we check if all hardware in status "Свободен"
            unavailable_hardware = self.get_unavailable_hardware()
        elif operation_id in [2, 3]:  # Employee "Сдал" или "Передал" in this case we check is the worker is the owner
            unavailable_hardware = self.check_owner()

        return unavailable_hardware

    @hybrid_method
    def get_unavailable_hardware(self):
        """
        Найдем по выборанным оборудованиям, те которые имеют статус 2 (Используется)
        :return unavailable_hardware: -> list(). Список кодов недоступных оборудований
        """
        unavailable_hardware = []
        result = self.session.query(HardwareUse.hardware_id, HardwareUse.status_id). \
            filter(HardwareUse.hardware_id.in_(self.hardware_id)).all()

        # Filter hardware with status "Используется"
        if result:
            unavailable_hardware = [row[0] for row in result if row[1] == 2]

        return unavailable_hardware

    @hybrid_method
    def check_owner(self):
        """
        Найдем по выбранным оборудованиям, у которых другой владелец
        :return diff_hardware: -> list(). Список кодов оборудований, у которых другой владелец
        """
        diff_hardware = []
        result = self.session.query(HardwareUse.hardware_id, HardwareUse.employee_id). \
            filter(HardwareUse.hardware_id.in_(self.hardware_id)).all()
        if result:
            # hardware which doesnt belong to owner
            diff_hardware = [row[0] for row in result if not row[1] == self.employee_id]

        return diff_hardware

    @hybrid_method
    def update_use_info(self, operation_id, worker_id, employee2_id=None):
        """
        Обновляет статус оборудования в таблице БД Hardware_use
        :param operation_id: Код операции оформления из таблицы Arrange_operations
        :param worker_id: Код пользователя, который оформляет из таблицы Workers
        :param employee2_id: Код пользователя, который получает или сдает оборудование из таблицы Workers
        :return:
        """
        # Статус на который меняется у оборудования в зависимости от кода операции
        # Например, если operation_id = 1 (Принял). Означает, что employee_id принимает оборудование и статус у
        # обоурудования должен поменяется на "Используется"
        operation_to_status_mapping = {
            1: 2,  # "Принял", "Используется"
            2: 1,  # "Сдал", "Свободен"
            3: 2,  # "Передал", "Используется"
        }
        status_to_change = operation_to_status_mapping[operation_id]

        hardware_list = self.session.query(HardwareUse).filter(HardwareUse.hardware_id.in_(self.hardware_id)).all()

        if hardware_list:
            for hardware in hardware_list:
                hardware.doc_date = self.doc_date
                hardware.status_id = status_to_change
                hardware.doc_num = self.doc_num
                # Если operation_id = 3 (Передал), значит employee_2 "Принял" оборудование у предыдущего сотрудника
                # Поэтому владельца оборудования нужно поменять на employee_2
                hardware.employee_id = employee2_id if operation_id == 3 else self.employee_id
                hardware.worker_id = worker_id

            self.session.commit()


class Hardware(Base):
    __tablename__ = 'hardware'
    __table_args__ = {'extend_existing': True}

    hardware_id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String)
    h_condition = Column('id_condition', Integer, ForeignKey('hardware_conditions.condition_id'))
    h_type = Column('id_type', Integer, ForeignKey('hardware_types.type_id'))
    h_brand = Column('id_brand', Integer, ForeignKey('brands.brand_id'))
    serial_num = Column(String)
    description = Column('descrip', String)
    validation_date = Column(Date, default=date.today)
    log_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    hardware_brand = relationship(Brand)
    hardware_condition = relationship(HardwareCondition)
    hardware_type = relationship(HardwareType)
    status = relationship('HardwareUse', primaryjoin='foreign(Hardware.hardware_id) == HardwareUse.hardware_id')

    def __init__(self, id_, name, id_condition, id_type, id_brand, serial, description, validation_date):
        self.hardware_id = id_
        self.name = name
        self.h_condition = id_condition
        self.h_type = id_type
        self.h_brand = id_brand
        self.serial_num = serial
        self.description = description
        self.validation_date = validation_date
