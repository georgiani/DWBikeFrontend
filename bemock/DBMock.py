from enum import Enum
import datetime
class Status(int, Enum):
    IN_USE = 0
    AVAILABLE = 1
    MAINTENANCE = 2
    RETIRED = 3

class MembershipType(int, Enum):
    STANDARD = 0
    PREMIUM = 1
    VIP = 2

class Currency(int, Enum):
    EURO = 0
    DOLLAR = 1
    RON = 3

class PaymentMethod(int, Enum):
    CARD = 0
    ACCOUNT = 1

class DBMock():
    def __init__(self):
        self.db = {
            "bikes": {},
            "rentals": {},
            "users": {
                "User1": {
                    "FN": "a",
                    "LN": "b",
                    "MembershipType": MembershipType.STANDARD
                }
            },
            "payments": {}
        }

    def addBike(self, bike_id, bike_type, bike_producer, tarif):
        self.db["bikes"][bike_id] = {
            "BikeID": bike_id,
            "BikeType": bike_type,
            "BikeProducer": bike_producer,
            "Status": Status.AVAILABLE,
            "Tarif": tarif
        }

    def getAllBikes(self):
        return self.db["bikes"]
    
    def getAllAvailableBikes(self):
        return { k:self.db["bikes"][k] for k in self.db["bikes"] if self.db["bikes"][k]["Status"] == Status.AVAILABLE }
    
    def checkAvailabilityOfBike(self, bike_id):
        return self.db["bikes"][bike_id]["Status"] == Status.AVAILABLE
    
    def addNewRental(self, user_id, bike_id, start_location):
        generated_rental_id = f"R{len(self.db["rentals"])}"
        self.db["rentals"][generated_rental_id] = {
            "user_id": user_id, 
            "bike_id": bike_id,
            "start_time": datetime.datetime.now(),
            "end_time": None,
            "start_location": start_location,
            "end_location": None
        }  

        self.db["bikes"][bike_id]["Status"] = Status.IN_USE

        return generated_rental_id
    
    def finishRental(self, rental_id, end_location):
        self.db["rentals"][rental_id]["end_time"] = datetime.datetime.now()
        self.db["rentals"][rental_id]["end_location"] = end_location 
        bike_id = self.db["rentals"][rental_id]["bike_id"]
        self.db["bikes"][bike_id]["Status"] = Status.AVAILABLE
    
    def getRentalsOfUser(self, user_id):
        return {k:self.db["rentals"][k] for k in self.db["rentals"] if self.db["rentals"][k]["user_id"] == user_id}

    def addPayment(self, rental_id, card_number_hint, payment_method, currency):
        generated_payment_id = f"R{len(self.db["payments"])}"

        bike_id = self.db["rentals"][rental_id]["bike_id"]
        user_id = self.db["rentals"][rental_id]["user_id"]

        bike_default_tarif = self.db["bikes"][bike_id]["Tarif"]
        user_membership_reduction = self.db["users"][user_id]["MembershipType"] / 10
        user_tarif = bike_default_tarif - user_membership_reduction * bike_default_tarif
        rental_start_time = self.db["rentals"][rental_id]["start_time"]
        rental_end_time = self.db["rentals"][rental_id]["end_time"]
        amount = int((rental_end_time - rental_start_time).total_seconds() / 60) * user_tarif

        self.db["payments"][generated_payment_id] = {
            "PaymentDate": rental_end_time,
            "Amount": amount,
            "CardNumberHint": card_number_hint,
            "PaymentMethod": payment_method,
            "Currency": currency
        }

        return amount