from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship


Base = automap_base()


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
    department = relationship(Department)

    def __init__(self, worker_id, name, department_id):
        self.worker_id = worker_id
        self.name = name
        self.department_id = department_id
