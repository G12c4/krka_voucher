from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Create a SQLAlchemy engine
room_engine = create_engine('sqlite:///rooms.db', echo=True)
employees_engine = create_engine('sqlite:///employees.db', echo=True)

# Create a declarative base
Base = declarative_base()

# Define the Room table
class Rooms(Base):
    __tablename__ = 'rooms'
    
    room_number = Column(Integer, primary_key=True)
    
    guests = relationship("Guest", back_populates="room")
    
    def __repr__(self):
        return f"<Rooms(room_number={self.room_number})>"

# Define the Guest table
class Guest(Base):
    __tablename__ = 'guests'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    date_of_birth = Column(String)
    room_number = Column(Integer, ForeignKey('rooms.room_number'))
    
    room = relationship("Rooms", back_populates="guests")
    
    def __repr__(self):
        return f"<Guest(id={self.id}, name='{self.name}', date_of_birth='{self.date_of_birth}', room_number={self.room_number})>"

# Define the Employee table  
class Employees(Base):
    __tablename__ = 'employees'
    
    employee_name = Column(String, primary_key=True)
    tickets_sold = Column(Integer)
    
    def __repr__(self):
        return f"<Employee(employee_name='{self.employee_name}', tickets_sold={self.tickets_sold})>"

# Create tables
# Base.metadata.create_all(room_engine)
# Base.metadata.create_all(employees_engine)

# Create a session
Session = sessionmaker(bind=room_engine)
Empl_session = sessionmaker(bind=employees_engine)
session = Session()
emp_session = Empl_session()

def delete_and_repopulate_data(guest_data: list[dict]):
    # Delete all existing entries
    session.query(Guest).delete()
    session.commit()
    
    # Add new guest entries
    guests = [
        Guest(name=guest["name"], date_of_birth=guest["dob"], room_number=guest["room"])
        for guest in guest_data
    ]
    session.add_all(guests)
    session.commit()
    session.close()

def add_employees(empl: list[str]):
    # Add new employee entries
    employees = [
        Employees(employee_name=employee, tickets_sold=0)
        for employee in empl
    ]
    emp_session.query(Employees).delete()
    emp_session.add_all(employees)
    emp_session.commit()

def add_tickets_sold(employee_name):
    # Find the employee by name
    employee = emp_session.query(Employees).filter_by(employee_name=employee_name).first()
    
    if employee:
        # Update the tickets_sold for the employee
        employee.tickets_sold += 1
        emp_session.commit()
        print(f"Added 1 ticket sold to employee: {employee_name}")
        emp_session.close()
    else:
        print(f"Employee not found: {employee_name}")

def get_guests_from_rooms(rooms):
    session = Session()
    guest_dict = {}
    for room_number in rooms:
        room = session.query(Rooms).filter_by(room_number=room_number).first()
        if room:
            guest_dict[room_number] = [{'name': guest.name, 'dob': guest.date_of_birth} for guest in room.guests]
    return guest_dict

def main():
    # Example usage
    guest_data = [
        {
            "room": "111",
            "name": "Josip Grcic",
            "dob": "08/09/1975"
        },
        {
            "room": "111",
            "name": "Mario Grcic",
            "dob": "03/11/1981"
        },
        {
            "room": "215",
            "name": "Daniel Grcic",
            "dob": "25/11/1961"
        },
        {
            "room": "215",
            "name": "Branka Grcic",
            "dob": "10/04/1964"
        }
    ]
    # delete_and_repopulate_data(guest_data=guest_data)
    
    # add_employees(["Josip Ercegovic","Daria Srsen", "Laura Mandusic"])

    # add_tickets_sold('Josip Ercegovic')
    # add_tickets_sold('Daria Srsen')
    # add_tickets_sold('Laura Mandusic')

    # rooms = [111]
    # guests = get_guests_from_rooms(rooms)
    # print(guests)

    # Close the session
    session.close()

if __name__ == "__main__":
    main()