from flask import Flask, jsonify, request
import datetime
from DBMock import DBMock, Currency, PaymentMethod

app = Flask(__name__)

db = DBMock()
db.addBike("B1", "Mountain", "P1", 0.5)
db.addBike("B2", "Electric", "P2", 1)

# Cerinta 1: scripturi de create table DB OLTP, Userii din DB, chestii necesare
# Cerinta 2: scripturi de generare date, cum le vezi si mai jos, B1, Producer1, etc
# Cerinta 3: scripturi de create table DB DW, la fel useri chestii. De tinut cont ca
#   DB-ul DW nu este facut pentru a fi updatat / sters de catre useri in vreun fel. 
#   rapoartele care se genereaza sunt read only si singurele modificari ar fi
#   adaugarea de entry-uri din OLTP in DW (sincronizare)
# Cerinta 4: Populare DW cu datele din OLTP: am mentionat cumva cum ar trebui sa 
#   fie transformate datele in Cerinta "Descriere Campuri" din sectiunea Analiza
#       Aici sa fie facuta o functie in Backend care ia entry-urile noi si complete
#       si face transformarile si le pune in celalalt db, backendul avand o comunicare
#       cu ambele db-uri.
# Cerinta 5: Definire constrangeri definite in Analiza (s-ar putea sa trebuiasca facut direct in analiza)
# Cerinta 6: Definire indecsi tot din analiza (tot in Analiza, sa fie aceeasi persoana)
# Cerinta 7: Obiecte dimension (tot din analiza).
# Toate cerintele din analiza sunt legate cu toate din Backend. Prin backend se face referire la 
#   DB mai mult decat 

@app.route("/getAllAvailableBikes", methods=["GET"])
def get_all_available_bikes():
    # call la db pentru bicicletele available
    resp = db.getAllAvailableBikes()
    return jsonify(resp), 200

@app.route("/getAllBikes", methods=["GET"])
def get_all_bikes():
    # call la db pentru bicicletele available
    resp = db.getAllBikes()
    return jsonify(resp), 200


@app.route("/checkAvailability", methods=["GET"])
def check_bike_availability():
    # /checkAvailability?bike=B1
    bike_id = request.args.get('bike_id')
    # verificare la latest inventory status, sa vezi daca e available, in use etc.
    # In momentul in care apesi pe o bicicleta se reverifica disponibilitatea. Mock pe always available
    
    return "1" if db.checkAvailabilityOfBike(bike_id) else "0", 200

@app.route("/getUserRentals", methods=["GET"])
def get_user_rentals():
    user_id = request.args.get("user_id")
    print(user_id)
    rentals = db.getRentalsOfUser(user_id)
    return jsonify(rentals), 200


@app.route("/startRental", methods=["POST"])
def start_rental():
    rental_params = request.get_json()
    user = "User1"
    bike_id = rental_params["bike_id"]
    location_start = rental_params["start_location"]
    # rental_params va avea 
    #   userul care a facut rentalul
    #   bicicleta asociata
    #   cand s-a inceput rentalul
    #   de unde a inceput rentalul

    # crearea unui entry in DB fara un end date sau end location
    # se returneaza rental_id

    rental_id = db.addNewRental(user, bike_id, location_start)
    return rental_id, 200

@app.route("/stopRental", methods=["POST"])
def stop_rental():
    rental_params = request.get_json()
    # la fel ca mai sus, dar se da end date si end location in loc de start date si start location + rental_id
    # 
    # dupa ce rentalul a fost modificat (acum avand toate campurile este terminat) se
    #   insererea si un payment care sa tina cumva de timp:
    current_rental_id = rental_params["rental_id"]
    location_end = rental_params["location_end"]
   
    # modificarea entry-ului, punand la end date data de la request si end location-ul dat. Aici se face si 
    #   introducerea unui Payment in tabela de payment care face referire la Rental-ul curent si cu suma aferenta 
    #   bicicletei si a timpului trecut de la StartDate
    db.finishRental(current_rental_id, location_end)
    amount = db.addPayment(current_rental_id, "************1234", PaymentMethod.CARD, Currency.EURO)

    return f"Rental and payment of {amount} succesful", 200

