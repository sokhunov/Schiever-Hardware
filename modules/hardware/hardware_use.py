from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session, relationship
from sqlalchemy import create_engine, null
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, text
from sqlalchemy.ext.hybrid import hybrid_method
from datetime import datetime, date
from modules.model_workers import Worker


Base = automap_base()


class ArrangeOperation(Base):
    """

    Таблица БД доступными типами операций оформления:

    1 =  Принял(а)
    2 = Сдал(а)
    3 = Передал(а)

    """

    __tablename__ = 'arrange_operations'

    operation_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))


class ArrangeStatus(Base):

    """

    Таблица БД с статусами оборудования:
    1 = Свободен
    2 = Используется

    """
    __tablename__ = 'arrange_statuses'

    arr_status_id = Column(Integer, primary_key=True)
    name = Column(String(50))


class HardwareUse(Base):
    """

    Таблица БД в которой хранится ПОСЛЕДНЯЯ информация о оборудованиях.
    Из этой таблицы можно получить информации:
    Доступно ли оборудование, на чье имя оборудование, номер акта, дата акта

    """

    __tablename__ = 'hardware_use'

    hardware_id = Column(primary_key=True, unique=True)
    employee_id = Column(Integer, ForeignKey('workers.worker_id'), nullable=True)
    status_id = Column(Integer, ForeignKey('arrange_statuses.arr_status_id'))
    doc_num = Column(Integer, nullable=True)
    doc_date = Column(Date, default=date.today)

    status = relationship(ArrangeStatus)
    employee = relationship(Worker)
    hardware = relationship()

    def __init__(self, hardware_id, session=None, employee_id=None, status_id=None, doc_num=None, doc_date=None):
        self.hardware_id = hardware_id
        self.session = session
        self.employee_id = employee_id
        self.status_id = status_id
        self.doc_num = doc_num
        self.doc_date = doc_date

    def __repr__(self):
        return f'{self.hardware_id} {self.status.name} {self.employee.name}'


Base.prepare()
