from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_method
from datetime import date, datetime
from modules.session_manager import load_session


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


class Hardware(Base):
    __tablename__ = 'hardware'
    __table_args__ = {'extend_existing': True}

    # -- DB table columns
    hardware_id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String)
    hardware_condition_id = Column('id_condition', Integer, ForeignKey('hardware_conditions.condition_id'))
    hardware_type_id = Column('id_type', Integer, ForeignKey('hardware_types.type_id'))
    hardware_brand_id = Column('id_brand', Integer, ForeignKey('brands.brand_id'))
    serial_num = Column(String)
    description = Column('descrip', String)
    validation_date = Column(Date, default=date.today)
    log_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    # -- relationships
    hardware_brand = relationship('Brand')
    hardware_condition = relationship('HardwareCondition')
    hardware_type = relationship('HardwareType')

    def __init__(self, id_: int, name: str, id_condition: int, id_type: int, id_brand: int, validation_date,
                 serial=None, description=None):
        self.hardware_id = id_
        self.name = name
        self.hardware_condition_id = id_condition
        self.hardware_type_id = id_type
        self.hardware_brand_id = id_brand
        self.validation_date = validation_date
        self.serial_num = serial
        self.description = description

    def __repr__(self):
        return f'Hardware(hardware_id={self.hardware_id}, name={self.name}, ' \
               f'hardware_condition_id={self.hardware_condition_id})'

    @hybrid_method
    def get_list_of_hardware(self):
        db_session = load_session()
        result = db_session.query(Hardware).all()
        return result


Base.prepare()