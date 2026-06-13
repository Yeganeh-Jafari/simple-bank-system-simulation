import sqlite3
import secrets
import hashlib, os
import datetime
import string
import random

class EAccount:
    chars = string.ascii_letters + string.digits + string.punctuation

    def __init__(self, a_username, a_balance, a_email, a_credit_card_number):
        self.balance = a_balance
        self.username = a_username
        self.email = a_email
        self.credit_card_number = a_credit_card_number


    def transfer(self, recipient_user, transfer_cash):
        if transfer_cash <= 0:
            return "transfer cash must be positive"

        if self.balance >= transfer_cash:
            self.balance -= transfer_cash
            recipient_user.balance += transfer_cash
            cur.execute("UPDATE users SET balance = ? WHERE username = ?", (self.balance, self.username))
            cur.execute("UPDATE users SET balance = ? WHERE username = ?", (recipient_user.balance, recipient_user.username))
            self.save_transaction(self.username, recipient_user.username, transfer_cash)
            conn.commit()
            print("transfer successful")

        else:
            print("not enough credit")

    def add_funds(self, cash):
        if cash <= 0:
            return "cash must be positive"
        self.balance += cash
        cur.execute("UPDATE users SET balance = ? WHERE username= ?", (self.balance, self.username))
        self.save_transaction(self.username, "deposit", cash)
        conn.commit()

    def draw_money(self, cash):
        if cash <= 0:
            return "cash must be positive"
        if self.balance >= cash:
            self.balance -= cash
            cur.execute("UPDATE users SET balance = ? WHERE username = ?", (self.balance, self.username))
            self.save_transaction(self.username, "output cash", cash)
            conn.commit()
        else:
            print("not enough credit")

    @staticmethod
    def is_card_num_duplicate(card_num):
        """make sure card_num is unique"""
        cur.execute("SELECT card_num FROM users WHERE card_num = ?", (card_num,))
        if cur.fetchone() is None:
            return False
        return True

    @classmethod
    def get_card_num(cls):

        while True:
            bank_identification_num = [6, 2, 2, 1, 0, 6]
            card_identification_num = [1, 2]
            serial_num_list = [random.randint(0, 9) for num in range(7)]

            card_num_list = bank_identification_num + card_identification_num + serial_num_list

            check_sum = 0
            check_number = 0
            # check to generate a valid credit card number
            for i, num in enumerate(reversed(card_num_list)):
                if i % 2 == 0:
                    num *= 2
                    if num >= 10: num -= 9

                check_sum += num

            while check_sum % 10 != 0:
                check_sum += 1
                check_number += 1

            card_num_list.append(check_number)
            card_num = "".join(map(str, card_num_list))

            if not cls.is_card_num_duplicate(card_num):
                return card_num

    def save_transaction(self, sender, reciever, cash):
        new_transaction = (sender, reciever, cash, datetime.datetime.now())
        cur.execute("INSERT INTO transactions VALUES (?, ?, ?, ?);", new_transaction)

    def show_transactions(self):
        cur.execute("SELECT * FROM transactions WHERE sender = ? OR reciever = ? ORDER BY time ;", (self.username, self.username))
        all_transactions = cur.fetchall()
        conn.commit()

        for transaction in all_transactions:
            print("-" * 50)
            print(
                f"from: {transaction[0]}\n"
                f"to: {transaction[1]}\n"
                f"amount: {transaction[2]}\n"
                f"time: {transaction[3]}\n"
            )

    @staticmethod
    def show_card_num(card_num):
        num_count = 0
        for num in card_num:
            num_count += 1
            print(num, end="")
            if num_count % 4 == 0 and num_count != 16:
                print("-", end="")
        print()

    @staticmethod
    def generate_pass():
        password_list = [secrets.choice(EAccount.chars) for _ in range(12)]
        return "".join(password_list)

    @staticmethod
    def hash_pass(password, salt):
        hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 10000)
        return hashed_password



conn = sqlite3.connect("ewallet.db")
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, balance INTEGER, email TEXT UNIQUE NOT NULL, password BLOB,salt BLOB, card_num TEXT);")
cur.execute("CREATE TABLE IF NOT EXISTS transactions(sender TEXT, reciever TEXT, amount INTEGER, time TEXT);")

conn.commit()

VALID_MAIN_MENU_OPTIONS = [str(num) for num in range(1, 4)]
VALID_ACCOUNT_MENU_OPTIONS = [str(num) for num in range(1, 7)]

while True:
    print("")
    print("welcome to python wallet".center(30, "="))
    print("")
    print(
        "1. register\n"
        "2. login\n"
        "3. exit"
    )

    choice = input("choice: ")
    print("")
    if choice not in VALID_MAIN_MENU_OPTIONS:
        print("please choose a number between 1 and 3".center(50, "!"))

    elif choice == "3":
        print("thank you for using python wallet".center(50, "-"))
        break

    elif choice == "1":
        try:
            user_name = input("please enter your username: ").strip()
            email = input("please enter your email: ").strip()
            password = input("please create a password: (type 0 to get a randomized password): ").strip()

            if user_name == "" or email == "" or password == "":
                print("\nplease do not leave any of the fields empty")
                continue

            if password == "0":
                password = EAccount.generate_pass()
                print(f"here is your randomized password: {password}\nplease do not share your password with anyone")
            else:
                if len(password) < 8:
                    print("\nyour password should atleast be 8 characters long")
                    continue



            card_num = EAccount.get_card_num()

            salt = os.urandom(32)

            hashed_password = EAccount.hash_pass(password, salt)

            new_user = (user_name, 100, email, hashed_password, salt, card_num)

            cur.execute("INSERT INTO users VALUES(?, ?, ?, ?, ?, ?);", new_user)
            conn.commit()

            print(f"register successful\nhere is your credit card number: ", end="")
            EAccount.show_card_num(card_num)

        except sqlite3.IntegrityError:
            print("\nerror, username or email already exists. please try again or try to sign in")

        except Exception as e:
            print("something went wrong", e)



    elif choice == "2":
        username = input("please enter your username: ")
        password = input("please enter your password: ")

        cur.execute("SELECT * FROM users WHERE username = ? ;", (username,))
        current_user_info = cur.fetchone()
        conn.commit()

        if current_user_info is None:
            print("no such username found")
            continue
        else:
            test_password = EAccount.hash_pass(password, current_user_info[4])
            if test_password == current_user_info[3]:
                current_user = EAccount(current_user_info[0], current_user_info[1], current_user_info[2],
                                     current_user_info[5])
            else:
                print("password is incorrect")
                continue

        while True:
            print("")
            print("your wallet".center(30, "="))
            print(
                f"balance: {current_user.balance}$\n\n"
                "1. transfer to account\n"
                "2. view transactions\n"
                "3. add funds\n"
                "4. draw cash\n"
                "5. my profile\n"
                "6. logout"
            )


            choice = input("choice: ")
            print("")

            if choice not in VALID_ACCOUNT_MENU_OPTIONS:
                print("please choose a number between 1 and 6".center(50, "!"))

            elif choice == "6":
                print("hope to see you soon".center(50, "-"))
                break

            elif choice == "4":
                try:
                    amount = int(input("how much cash do you need: $"))
                    if amount > 0:
                        current_user.draw_money(amount)
                    else:
                        print("amount should be a positive number greater than zero")

                except ValueError:
                    print("please enter a valid amount")


            elif choice == "3":
                try:
                    amount = int(input("how much do you want to add?: $"))
                    if amount > 0:
                        current_user.add_funds(amount)
                    else:
                        print("amount should be a positive number greater than zero")

                except ValueError:
                    print("please enter a valid amount")


            elif choice == "2":
                current_user.show_transactions()

            elif choice == "1":

                recipient_card_num = input("recipient credit card number: ")
                try:
                    amount = int(input("amount: $"))
                except ValueError:
                    print("please enter a valid amount")
                else:
                    if amount > 0 :
                        cur.execute("SELECT * FROM users WHERE card_num = ?", (recipient_card_num,))
                        recipient_info = cur.fetchone()
                        if recipient_info is None:
                            print("invalid destination")
                        else:
                            recipient = EAccount(recipient_info[0], recipient_info[1], recipient_info[2],
                                                       recipient_info[5])

                            check = input(f"transfer {amount} to {recipient.username}?(yes/no): ")
                            if check == "yes":
                                current_user.transfer(recipient, amount)

                            else:
                                print("transfer cancelled")
                    else:
                        print("amount should be a positive number greater than zero")

cur.close()
conn.close()
