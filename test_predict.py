from app.ml.predict import predict_crops

print('Farmer John, Nakuru:')
r = predict_crops(21, 1100, 1800, 'Loamy', 6.5)
for i, x in enumerate(r[:5]):
    star = 'BEST CHOICE' if i == 0 else ''
    print(' ', x['crop'], '-', x['percentage'], '%', star)

print()
print('Farmer Mary, Machakos:')
r = predict_crops(28, 600, 1000, 'Sandy', 6.0)
for i, x in enumerate(r[:5]):
    star = 'BEST CHOICE' if i == 0 else ''
    print(' ', x['crop'], '-', x['percentage'], '%', star)

print()
print('Farmer Peter, Nyeri:')
r = predict_crops(14, 1000, 2000, 'Loamy', 6.2)
for i, x in enumerate(r[:5]):
    star = 'BEST CHOICE' if i == 0 else ''
    print(' ', x['crop'], '-', x['percentage'], '%', star)