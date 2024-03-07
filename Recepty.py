import tkinter as tk
from tkinter import messagebox, ttk
import pyodbc
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import barcode
from barcode.writer import ImageWriter
import random
from datetime import datetime

def generate_pdf(data):
    try:
        pdf_file = "recepta.pdf"
        c = canvas.Canvas(pdf_file, pagesize=letter)

        # Rejestrujemy czcionkę polską w formacie TTF
        pdfmetrics.registerFont(TTFont('PolishFont', 'PolishFont.ttf'))

        c.setFont("PolishFont", 18)  # Ustawienie czcionki dla tekstu

        c.drawString(100, 750, "Recepta")
        y = 750
        page_height = 750  # Wysokość strony PDF
        for row in data:
            c.setFont("PolishFont", 14)
            c.drawString(100, y - 20, "Pacjent: {} {}".format(row['PacjentImie'], row['PacjentNazwisko']))  
            c.drawString(100, y - 40, "Lekarz: {} {}".format(row['LekarzImie'], row['LekarzNazwisko']))  
            data_wystawienia = datetime.strptime(row['DataWystawienia'], "%Y-%m-%d")
            c.drawString(100, y - 60, "Data Wystawienia: {}".format(data_wystawienia.strftime("%Y-%m-%d")))
            c.drawString(100, y - 80, "Nazwa Leku: {}".format(row['NazwaLeku']))
            c.drawString(100, y - 100, "Dawka: {}".format(row['Dawka']))
            c.drawString(100, y - 120, "Częstotliwość: {}".format(row['Czestotliwosc']))
            c.drawString(100, y - 140, "Ilość opakowań: {}".format(row['IloscOpakowan']))

            barcode_value = str(random.randint(100000000000, 999999999999))  
            code128 = barcode.get_barcode_class('code128')
            code = code128(barcode_value, writer=ImageWriter())
            barcode_file = "barcode"
            code.save(barcode_file)
            c.drawImage(barcode_file + ".png", 400, y - 110, width=200, height=125)
            
            y -= 180  # Przesuń pionową pozycję do narysowania kolejnej recepty

            # Sprawdź, czy wystarcza miejsca na rysowanie kolejnej recepty na tej stronie PDF
            if y < 20:
                c.showPage()  # Utwórz nową stronę PDF
                c.setFont("PolishFont", 18)  # Ustawienie czcionki dla tekstu
                c.drawString(100, page_height, "Recepta")  # Dodaj nagłówek na nowej stronie
                y = page_height  # Przypisz wysokość strony do zmiennej y, aby zacząć rysowanie od góry
        c.drawString(100, 100, "Podpis lekarza: _______________")
        c.save()
        messagebox.showinfo("Sukces", "Recepta została wygenerowana pomyślnie.")
    except Exception as e:
        messagebox.showerror("Błąd", f"Błąd podczas generowania recepty: {e}")

def get_dates(patient_id):
    try:
        connection = pyodbc.connect('DRIVER={SQL Server};SERVER=.;DATABASE=Przychodnia;Trusted_Connection=yes;')
        cursor = connection.cursor()
        cursor.execute("""SELECT DISTINCT DataWystawienia
                          FROM Recepta
                          WHERE PacjentID = ?;""", (patient_id,))
        dates = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return dates
    except Exception as e:
        messagebox.showerror("Błąd", f"Błąd podczas pobierania dat recept: {e}")


def select_patient():
    patient_id = entry_patient_id.get()
    if patient_id:
        dates = get_dates(patient_id)
        if dates:
            # Okno dialogowe z Combobox'em
            select_date_window = tk.Toplevel(root)
            select_date_window.title("Wybierz datę recepty")
            select_date_window.geometry("300x125")  # Zwiększenie szerokości okna

            # Utworzenie ramki dla elementów interfejsu
            frame_select_date = tk.Frame(select_date_window, padx=20, pady=10)
            frame_select_date.pack()

            label_select_date = tk.Label(frame_select_date, text="Wybierz datę recepty:")
            label_select_date.grid(row=0, column=0)

            combo_dates = ttk.Combobox(frame_select_date, values=dates)
            combo_dates.grid(row=0, column=1, padx=10)

            def close_window():
                try:
                    if select_date_window.winfo_exists():  # Sprawdź, czy okno istnieje
                        select_date_window.destroy()
                except tk.TclError:
                    pass

            button_select_date = tk.Button(frame_select_date, text="Wybierz", command=lambda: [generate_invoice(patient_id, combo_dates.get()), close_window()])
            button_select_date.grid(row=1, column=0, columnspan=2, pady=10)

        else:
            messagebox.showerror("Błąd", "Brak danych recepty dla podanego pacjenta.")
    else:
        messagebox.showwarning("Ostrzeżenie", "Wprowadź identyfikator pacjenta.")

def generate_invoice(patient_id, selected_date):
    if selected_date:
        data = execute_query(patient_id, selected_date)
        if data:
            generate_pdf(data)
            root.destroy()  # Zamknięcie głównego okna aplikacji po poprawnym wykonaniu operacji
        else:
            messagebox.showerror("Błąd", "Brak danych recepty dla wybranej daty.")
    else:
        messagebox.showwarning("Ostrzeżenie", "Wybierz datę recepty.")

def execute_query(patient_id, selected_date):
    try:
        connection = pyodbc.connect('DRIVER={SQL Server};SERVER=.;DATABASE=Przychodnia;Trusted_Connection=yes;')
        cursor = connection.cursor()
        cursor.execute("""SELECT R.ReceptaID, R.PacjentID, R.DataWystawienia, R.NazwaLeku, R.Dawka, R.Czestotliwosc, R.IloscOpakowan,
       L.Imie AS LekarzImie, L.Nazwisko AS LekarzNazwisko,
       P.Imie AS PacjentImie, P.Nazwisko AS PacjentNazwisko
FROM Recepta AS R
JOIN Lekarz AS L ON R.LekarzID = L.LekarzID
JOIN Pacjent AS P ON R.PacjentID = P.PacjentID
WHERE R.PacjentID = ? AND R.DataWystawienia = ?;""", (patient_id, selected_date))
        data = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return data
    except pyodbc.Error as e:
        messagebox.showerror("Błąd", f"Błąd podczas wykonywania zapytania SQL: {e}")
        return None

root = tk.Tk()
root.title("Generator Recept")

# Ustawienie rozmiarów okna głównego
root.geometry("300x125")

# Dodanie marginesów do elementów interfejsu użytkownika
frame_patient_id = tk.Frame(root, padx=20, pady=10)
frame_patient_id.pack()

label_patient_id = tk.Label(frame_patient_id, text="ID Pacjenta:")
label_patient_id.grid(row=0, column=0)

entry_patient_id = tk.Entry(frame_patient_id)
entry_patient_id.grid(row=0, column=1)

button_generate = tk.Button(root, text="Generuj receptę", command=select_patient)
button_generate.pack(pady=10)

root.mainloop()
