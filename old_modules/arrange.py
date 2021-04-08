from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func
from sqlalchemy.ext.hybrid import hybrid_method
from datetime import datetime, date

Base = automap_base()


class ArrangeOperation(Base):
    """
    Arrange operations types:
        1 = Принял(а)
        2 = Сдал(а)
        3 = Передал(а)
    """

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
    __tablename__ = 'arrange_statuses'

    arr_status_id = Column(Integer, primary_key=True)
    name = Column(String(50))

    def __repr__(self):
        return f'ArrangeStatus(id={self.arr_status_id}, name={self.name})'


class ArrangeHardware(Base):
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
    operation = relationship('ArrangeOperation', viewonly=True)
    it_worker = relationship('Worker', foreign_keys=[it_worker_id])

    def __init__(self, **kwargs):
        self.hardware_id = [int(h_id) for h_id in kwargs['hardware_id']]
        self.it_worker_id = int(kwargs['it_worker'][0])
        self.employee_id = int(kwargs['employee_id'][0])
        self.operation_id = int(kwargs['operation_id'][0])
        self.doc_num = kwargs['doc_num'][0]
        self.doc_date = kwargs['doc_date'][0]
        self.employee2_id = int(kwargs['employee_2'][0]) if kwargs.get('employee_2') else None
        self.db_session = smanager.load_session()

    def arrange(self):
        missing_hardware = self.get_missing_hardware()

        if missing_hardware:
            self.create_hardware(missing_hardware)

    @hybrid_method
    def get_missing_hardware(self) -> list:
        missing_hardware = []
        result = self.db_session.query(hard.Hardware).filter(hard.Hardware.hardware_id.in_(self.hardware_id)).all()
        if result:
            for hardware in result:
                if not hardware.hardware_use:
                    missing_hardware.append(hardware)
        else:
            missing_hardware.extend(result)

        return missing_hardware

    @hybrid_method
    def create_hardware(self, hardware_to_create):
        hardware_list = []
        for hardware in hardware_to_create:
            hardware_use = HardwareUse(hardware_id=hardware.hardware_id)
            hardware.hardware_use.append(hardware_use)
            hardware_list.append(hardware)

        self.db_session.add_all(hardware_list)
        self.db_session.commit()


class PreArrange:
    def __init__(self, hardware):
        self.db_session = smanager.load_session()
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
            return self.db_session.query(work.Worker).filter(work.Worker.department_id == 1).all()
        else:
            return self.db_session.query(work.Worker).filter(work.Worker.department_id != 1).all()

    def get_next_doc_num(self):
        """
        Get the last document number from DB table HardwareUse
        :return:
        """
        last_doc_num = self.db_session.query(func.max(hard_use.HardwareUse.doc_num)).scalar()
        if not last_doc_num:
            return 1

        return last_doc_num

    def get_arrange_operations(self):
        return self.db_session.query(ArrangeOperation).all()

    def get_selected_hardware(self, hardware_id: list):
        return self.db_session.query(hard.Hardware).filter(hard.Hardware.hardware_id.in_(hardware_id)).all()


Base.prepare()