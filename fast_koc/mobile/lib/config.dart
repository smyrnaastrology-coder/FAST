// Fast Koç — ortak ayar + oturum.
const String fastKocBaseUrl = String.fromEnvironment(
  'FASTKOC_API_URL',
  defaultValue: 'http://10.0.2.2:8090', // Android emulator -> PC localhost
);

class Session {
  static int? ogrenciId;
  static String? ogrenciAd;
  static String? segment;
  static String? token;
}
