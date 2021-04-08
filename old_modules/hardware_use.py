from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Date, ForeignKey
from datetime import date
import old_modules.hardware as hard


Base = automap_base()


class HardwareUse(Base):
    """

    Таблица БД в которой хранится ПОСЛЕДНЯЯ информация о оборудованиях.
    Из этой таблицы можно получить информации:
    Доступно ли оборудование, на чье имя оборудование, номер акта, дата акта

    """

    __tablename__ = 'hardware_use'

    hardware_id = Column(Integer, ForeignKey(hard.Hardware.hardware_id), primary_key=True, unique=True)
    employee_id = Column(Integer, ForeignKey(hard.Worker.worker_id), nullable=True)
    status_id = Column(Integer, ForeignKey(ArrangeStatus.arr_status_id), default=1)
    doc_num = Column(Integer, nullable=True)
    doc_date = Column(Date, default=date.today)

    status = relationship('ArrangeStatus', viewonly=True)
    employee = relationship('Worker', viewonly=True)

    def __repr__(self):
        return f'{self.hardware_id}-{self.hardware.name}, status {self.status.name}'


Base.prepare()
