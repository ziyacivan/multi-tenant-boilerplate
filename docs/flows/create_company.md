## Şirket Oluşturma İş Akışı
1. Bir kullanıcının şirket oluşturabilmesi için rolünün `owner` olması gerekmektedir.
2. `owner` rolündeki kullanıcı şirket oluşturma isteğini gönderdiğinde, hali hazırda başka bir şirket ile ilişkisinin olmaması gerekir.
    - Bu kullanıcının yeni bir kullanıcı olduğunu tanımlar.
3. Oluşturulan şirket bilgileri, backend tarafından belirlenmiş ve frontend tarafından gönderilmiş verilerle oluşturulur.
4. Şirket oluşturulduktan sonra kullanıcının şirket şemasındaki izinleriyle ilgili bir problem olması (senkronizasyonu) sorununda aşağıdaki bağlantıda yer alan implementasyon çağrılabilir:
    - https://github.com/blackrock-studio/hrm-api/blob/main/docs/setup.md#tenant-schemas%C4%B1-i%CC%87%C3%A7erisinde-operasyonlar

### İstek Gönderilecek Şema
1. Kullanıcıların tamamı aslında ana uygulama içerisinde birer kullanıcıdır. Bu nedenle, her kullanıcının `public` şemasında bir kaydı bulunmaktadır.
2. Kullanıcının şirket oluşturma isteğini ana uygulama içerisinden göndermesi gerekir, örnek: `hrmore.com`
