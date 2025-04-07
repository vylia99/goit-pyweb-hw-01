from collections import UserDict
from datetime import datetime, timedelta
import pickle
from abc import ABC, abstractmethod

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain exactly 10 digits.")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)
    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        phone_to_remove = self.find_phone(phone)
        if phone_to_remove:
            self.phones = [ph for ph in self.phones if ph.value != phone]
        else:
            raise ValueError(f"Phone number {phone} not found.")

    def edit_phone(self, old_phone, new_phone):
        if not new_phone.isdigit() or len(new_phone) != 10:
            raise ValueError(f"New phone number {new_phone} is invalid. It must contain exactly 10 digits.")

        phone_to_edit = self.find_phone(old_phone)
        if phone_to_edit:
            self.remove_phone(old_phone)
            self.add_phone(new_phone)
        else:
            raise ValueError(f"Old phone number {old_phone} does not exist.")

    def find_phone(self, phone):
        for ph in self.phones:
            if ph.value == phone:
                return ph
        return None

    def __str__(self):
        birthday_info = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}{birthday_info}"


class AddressBook(UserDict):

    def __init__(self):
        self.records = {}

    def add_record(self, record):
        self.records[record.name.value] = record

    def find(self, name):
        return self.records.get(name)

    def get_all_contacts(self):
        return "\n".join(str(record) for record in self.records.values())

    def delete(self, name):
        if name in self.records:
            del self.records[name]
        else:
            raise ValueError(f"Record with name {name} not found.")

    def adjust_for_weekend(self, date):
        if date.weekday() >= 5:  # 5 - Saturday, 6 - Sunday
            return self.find_next_weekday(date, 0)  # Перенос на ближайший понедельник
        return date

    def find_next_weekday(self, start_date, weekday):
        days_ahead = (weekday - start_date.weekday()) % 7
        return start_date + timedelta(days=days_ahead)
    @property
    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.records.values():
            if record.birthday:
                birthday_date = datetime.strptime(record.birthday.value, "%d.%m.%Y").replace(year=today.year)
                if birthday_date.date() < today:
                    birthday_date = birthday_date.replace(year=today.year + 1)
                days_until_birthday = (birthday_date.date() - today).days
                if 0 <= days_until_birthday <= 7:
                    birthday_date = self.adjust_for_weekend(birthday_date.date())
                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "birthday": birthday_date.strftime("%d.%m.%Y")
                    })

        return upcoming_birthdays

    def __str__(self):
        return "\n".join(str(record) for record in self.records.values())


def input_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, IndexError) as e:
            return f"Error: {str(e)}"
    return wrapper

@input_error
def add_contact(args, book):
    name, phone = args[:2]
    record = book.find(name)
    if not record:
        record = Record(name)
        book.add_record(record)
    record.add_phone(phone)
    return "Contact added"

@input_error
def edit_contact(args, book):
    name, old_phone, new_phone = args[:3]
    record = book.find(name)
    if not record:
        return "Contact not found"
    record.edit_phone(old_phone, new_phone)
    return "Contact updated"

@input_error
def find_phone(args, book):
    name = args[0]
    record = book.find(name)
    if not record or not record.phones:
        return "Phone not found"
    return f"Phone number {name}: {','.join(str(phone) for phone in record.phones)}"

@input_error
def show_all(book):
    return book.get_all_contacts()

@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find(name)
    if not record:
        return "Birthday not found"
    record.add_birthday(birthday)
    return "Birthday added"

@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find(name)
    if not record or not record.birthday:
        return "Birthday not found"
    return f"Birthday {name} is {record.birthday}"

@input_error
def show_birthdays(book):
    birthdays = book.get_upcoming_birthdays
    return "\n".join(f"{b['name']} - with {b['birthday']}" for b in birthdays) if birthdays else "There are no birthdays for the next week."


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

class UserInterface(ABC):

    @abstractmethod
    def show_message(self, message: str):
        pass

    @abstractmethod
    def get_input(self, prompt: str) -> str:
        pass

    @abstractmethod
    def show_error(self, message: str):
        pass

class ConsoleInterface(UserInterface):

    def show_message(self, message: str):
        print(message)

    def get_input(self, prompt: str) -> str:
        return input(prompt)

    def show_error(self, message: str):
        print(f"Error: {message}")



def main():
    ui = ConsoleInterface()
    book = load_data()
    ui.show_message("Ласкаво просимо до бота-помічника!")
    ui.show_message("Доступні доманди: add, change, phone, all, add-birthday, show-birthday, birthdays, hello, close or exit")
    while True:
        user_input = ui.get_input("Введіть команду: ")
        if not user_input:
            ui.show_message("Введіть команду.")
            continue

        command, *args = user_input.split()
        command = command.lower()
        if command in ["close", "exit"]:
            save_data(book)
            ui.show_message("До побачення!")
            break

        elif command == "hello":
            ui.show_message("Чим я можу вам допомогти?")

        elif command == "add":
            ui.show_message(add_contact(args, book))

        elif command == "change":
            ui.show_message(edit_contact(args, book))

        elif command == "phone":
            ui.show_message(find_phone(args, book))

        elif command == "all":
            ui.show_message(show_all(book))

        elif command == "add-birthday":
            ui.show_message(add_birthday(args, book))

        elif command == "show-birthday":
            ui.show_message(show_birthday(args, book))

        elif command == "birthdays":
            ui.show_message(show_birthdays(book))

        else:
            ui.show_error("Недійсна команда.")

if __name__ == "__main__":
    main()
