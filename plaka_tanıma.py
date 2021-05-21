import numpy as np
import cv2
import imutils
import sys
import pytesseract
from tkinter import *
from tkinter import messagebox
import pandas as pd
import time
import sqlite3
import random
import datetime

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
cam = cv2.VideoCapture("Videolar/plakavideo2.mp4")

#VERİ TABANI BAĞLANTISI
con = sqlite3.connect("plaka.db")
cursor = con.cursor()

#TKİNTER ARAYÜZÜ
master =Tk()
master.title("Plaka Tanıma Sistemi")
master.geometry("600x1200")

# formu grid olarak çizdirme layout
uygulama = Frame(master, )
uygulama.grid()

listbox = Listbox(uygulama)
#listbox 

def main():
    s = 1
    while True:
        ret, image = cam.read()
        image = imutils.resize(image)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray, 11, 17, 17)
        edged = cv2.Canny(gray, 170, 200)
        (cnts, _) = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE) 
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
        NumberPlateCnt = None
        count = 0
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4:
                NumberPlateCnt = approx
                break
            
        #PLAKA ÇERÇEVESİ MASKELEME
        mask = np.zeros(gray.shape, np.uint8)
        Simage = cv2.drawContours(mask, [NumberPlateCnt], 0, 255, -1)
        Simage = cv2.bitwise_and(image, image, mask=mask)
        cv2.namedWindow("Plaka", cv2.WINDOW_NORMAL)
        cv2.imshow("Plaka", Simage)
        
        # TESSEARCT İLE HARFLER TANIMLANIYOR
        config = ('-l eng --oem 1 --psm 3')
        
        # GÖRÜNTÜDE TESSERACT OCR ÇALIŞTIRILIR
        text = pytesseract.image_to_string(Simage, config=config)
        print(text)
        plaka = str(text)
        
        def update():
            #OKUNAN PLAKANIN GİRİŞ ÇIKIŞ SAATİ GÜNCELLEME

            cursor.execute("SELECT Durum FROM Kontrol WHERE Plaka='{}' ".format(plaka))
            upt = cursor.fetchall()#durum bilgisini çekiyor
            print(upt)
            for i in upt:
                st = str(i)#durumu stringe çeviriyor
                zaman = time.time()
                tarih = str(datetime.datetime.utcfromtimestamp(zaman).strftime('%Y-%m-%d %H:%M:%S'))#okunduğu zaman tarihi yazıyor
                if (st == "(1,)"):
                    cursor.execute("UPDATE Kontrol SET Durum=0 WHERE Plaka='{}' ".format(plaka))
                    cursor.execute("UPDATE Kontrol SET Cikis_t='{}' ".format(tarih) + " WHERE Plaka='{}' ".format(plaka))
                    Door = Label(uygulama, text="Çıkış Yapıldı. ", font=("Ariel", 12))
                    Door.grid(row=1, column=0, padx=155, sticky=W, pady=5, columnspan=2) #konumlandırma
                    
                    
                elif (st == "(0,)"):
                    cursor.execute("UPDATE Kontrol SET Durum=1 WHERE Plaka='{}' ".format(plaka))
                    cursor.execute("UPDATE Kontrol SET Giris_t='{}' ".format(tarih) + " WHERE Plaka='{}' ".format(plaka))
                    Door = Label(uygulama, text="Giriş Yapıldı. ", font=("Ariel", 12)) #uygulama frame
                    Door.grid(row=1, column=0, padx=155, sticky=W, pady=5, columnspan=2)

                else:
                    print("Plaka tanımlı değil.")
                    Door = Label(uygulama, text="Plaka Kayıtlı Değil. ", font=("Ariel", 12))
                    Door.grid(row=1, column=0, padx=155, sticky=W, pady=5, columnspan=2)
                con.commit()
                
         # Data CSV dosyasında saklanır
        if text:
            #OKUNAN ARACI TKİNDERDA GÖSTERME
            O_arac = Label(uygulama, text="Araç: " + plaka, font=("Ariel", 15, "bold"), foreground="#b10000")
            O_arac.grid(row=0, column=0, padx=50, sticky=W, pady=2, columnspan=2)
            
            update()
            """EXCELE KAYIT
            raw_data = {'date': [time.asctime(time.localtime(time.time()))], '': [text]}
            df = pd.DataFrame(raw_data)
            df.to_csv('data.csv', mode='a')
            print("excel kaydı başarılı")"""
        else:
            Door = Label(uygulama, text="Plaka Kayıtlı Değil. ", font=("Ariel", 12))
            Door.grid(row=1, column=0, padx=155, sticky=W, pady=5, columnspan=2)
        s = s - 1
        if s == 0:
            break

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    def listele():
        #TÜM ARAÇLARI LİSTELE
        listbox.delete(0, END)
        cursor.execute("SELECT * FROM Kontrol")
        data = cursor.fetchall()# VERİTABANINDAKİ VERİLERİ ÇEKİYOR
        a=0
        for i in data:
            a += 1
            listbox.insert(a, i)
            listbox.grid(row=10,column=0, padx=2, ipadx=150, ipady=2)
            
        def excelListe():
            for i in data:
                # EXCELE GENEL KAYIT
                raw_data = {'Tarih': [time.asctime(time.localtime(time.time()))], '': [i]}
                df = pd.DataFrame(raw_data)
                df.to_csv('liste.csv', mode='a')
            print("excel kaydı başarılı")
            messagebox.showinfo("Bilgi","Kayıt Başarılı.")

        excelRapor = Button(uygulama, bg="#add8e6", text=" EXCEL ",font=("Ariel", 9, "bold"),fg="#f2f2f2", width=14, height=1, command=excelListe)
        excelRapor.grid(row=15, column=0, padx=150, pady=2)
        
    def tarihListele():
        #GİRİLEN TARİHE GÖRE LİSTELE
        listbox.delete(0, END)
        nTarih = tL.get()
        if(nTarih):
            cursor.execute("SELECT * FROM Kontrol WHERE Giris_t BETWEEN '"+nTarih+" 00:00:00' AND '"+nTarih+"23:59:59'")
            data = cursor.fetchall()
            a=0
            if(data):
                for i in data:
                    a += 1
                    listbox.insert(a, i)
                    listbox.grid(row=10, ipadx=150, ipady=2)
            else:
                messagebox.showinfo("Uyarı", "Lütfen Tarihi YYYY-AA-GG Formatında giriniz!")
        else:
            messagebox.showinfo("Uyarı", "Lütfen Tarihi Giriniz!")
            
    def plakaListele():
        #PLAKAYA GÖRE LİSTELE
        listbox.delete(0, END)
        nPlaka = pL.get()
        if(nPlaka):
            cursor.execute("SELECT * FROM Kontrol WHERE Plaka ='"+nPlaka+"'" )
            data = cursor.fetchall()
            if(data):
                listbox.insert(1, data)
                listbox.grid(row=10, ipadx=150, ipady=2)
            else:
                messagebox.showinfo("Uyarı", "Plaka bulunamadı. Lütfen Plakayı Kontrol Ediniz!")

        else:
            messagebox.showinfo("Uyarı", "Lütfen Plakayı Giriniz!")
            
    def iceri():
        # İÇERİDEKİ ARAÇLARI LİSTELE
        listbox.delete(0, END)
        cursor.execute("SELECT * FROM Kontrol WHERE Durum=1")
        data = cursor.fetchall()
        a = 0
        for i in data:
            a += 1
            listbox.insert(a, i)
            listbox.grid(row=10, column=0, padx=2, ipadx=150, ipady=2)

    def Kayit():
        def Kaydet():
            N_plaka = e1.get()
            N_ad = e2.get()
            N_soyad = e3.get()
            print(N_plaka, N_ad, N_soyad)
            Kaydi = Label(uygulama, text=N_plaka + " " + N_ad + "" + N_soyad)
            Kaydi.grid(row=16, column=0, padx=20, pady=2)
            Giris_t = ""
            Cikis_t = ""
            Ad = N_ad
            Soyad = N_soyad
            Plaka = N_plaka
            Durum = True
            cursor.execute("INSERT INTO Kontrol(Plaka,Ad,Soyad,Giris_t,Cikis_t,Durum) VALUES(?,?,?,?,?,?)",
                           (Plaka, Ad, Soyad, Giris_t, Cikis_t, Durum))
            con.commit()
            
        # etiket widgeti oluşturma
        l1 = Label(uygulama, text="Plaka: ", font=("Ariel", 10, "bold"))
        l2 = Label(uygulama, text="Ad: ", font=("Ariel", 10, "bold"))
        l3 = Label(uygulama, text="Soyad: ", font=("Ariel", 10, "bold"))
        
        # ilgili etiketleri düzenlemek için ızgara yöntemi
        l1.grid(row=12, column=0, sticky=W, pady=2, padx=60)
        l2.grid(row=13, column=0, sticky=W, pady=2, padx=60)
        l3.grid(row=14, column=0, sticky=W, pady=2, padx=60)
        
        # kullanıcıdan giriş almak için kullanılan giriş widget'ları
        e1 = Entry(uygulama)
        e2 = Entry(uygulama)
        e3 = Entry(uygulama)
        
        # giriş widget'larını düzenleyecek
        e1.grid(row=12, column=0, pady=2)
        e2.grid(row=13, column=0, pady=2)
        e3.grid(row=14, column=0, pady=2)

        buton = Button(uygulama)
        buton.config(text=u"Kaydet", bg="#add8e6",fg="#f2f2f2",font=("Ariel", 10, "bold"), command=Kaydet)
        buton.grid(row=15, column=0, padx=10, pady=2)
        
         #---------------------- LİSTELEME BUTONLARI---------------------#
         #---------------------------------------------------------------#
    TumunuListele = Button(uygulama, bg="#add8e6", text=" Araçları Listele ",font=("Ariel", 9, "bold"),fg="#f2f2f2", width=14, height=1, command=listele)
    TumunuListele.grid(row=3, column=0, padx=155, pady=5)
    iceridekiler = Button(uygulama, bg="#add8e6", text=" İçerideki Araçlar ", font=("Ariel", 9, "bold"), fg="#f2f2f2",width=14, height=1, command=iceri)
    iceridekiler.grid(row=4, column=0, padx=155, pady=5)
    PlakaLabel = Label(uygulama, text="Plaka: ",width=12, height=1, font=("Ariel", 10, "bold")).grid(row=5, column=0, sticky=W, pady=2, padx=60)
    pL = Entry(uygulama)
    pL.grid(row=5, column=0, pady=2, padx=155)
    PlakaListele = Button(uygulama, font=("Ariel", 9), bg="#add8e6",fg="#f2f2f2")
    PlakaListele.config(text="Listele ", width=12, height=1, command=plakaListele)
    PlakaListele.grid(row=6, column=0, pady=20, padx=155)

    TarihLabel = Label(uygulama, text="Tarih: ", width=12, height=1, font=("Ariel", 10, "bold")).grid(row=7, column=0, sticky=W, pady=2, padx=60)
    tL = Entry(uygulama)
    tL.grid(row=7, column=0, pady=2, padx=155)
    TarihListele = Button(uygulama, font=("Ariel", 9), bg="#add8e6",fg="#f2f2f2")
    TarihListele.config(text=u"Listele ", width=12, height=1, command=tarihListele)
    TarihListele.grid(row=8, column=0, pady=2, padx=155)


    menubar = Menu(master)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Araç Kaydet", command=Kayit)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=master.quit)
    menubar.add_cascade(label="File", menu=filemenu)

    master.config(menu=menubar)
    
    #TKİNTER PENCERESİNİ KAPATTIK
    master.mainloop()

if __name__ == "__main__":
 main()
con.close()
