import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';

/// Üyelik durumunu takip eden ChangeNotifier.
enum AuthStatus { unknown, signedOut, signedIn }

class AuthProvider extends ChangeNotifier {
  AuthStatus _status = AuthStatus.unknown;
  String? _error;
  bool _busy = false;

  AuthStatus get status => _status;
  bool get isLoggedIn => _status == AuthStatus.signedIn;
  bool get isBusy => _busy;
  bool get enabled => AuthService.enabled;
  String? get error => _error;
  String get email => AuthService.email;

  static AuthProvider of(BuildContext context) =>
      Provider.of<AuthProvider>(context, listen: false);

  /// Uygulama açılışında çağrılır.
  Future<void> restore() async {
    AuthService.onSessionChanged = () {
      _status = AuthService.isLoggedIn ? AuthStatus.signedIn : AuthStatus.signedOut;
      notifyListeners();
    };
    await AuthService.init();
    _status = AuthService.isLoggedIn ? AuthStatus.signedIn : AuthStatus.signedOut;
    notifyListeners();
  }

  Future<bool> _run(Future<void> Function() action) async {
    _busy = true;
    _error = null;
    notifyListeners();
    try {
      await action();
      _status = AuthService.isLoggedIn ? AuthStatus.signedIn : AuthStatus.signedOut;
      notifyListeners();
      return true;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return false;
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  Future<bool> signUp({required String email, required String password}) =>
      _run(() => AuthService.signUp(email: email, password: password));

  Future<bool> signIn({required String email, required String password, bool remember = true}) =>
      _run(() => AuthService.signIn(email: email, password: password, remember: remember));

  Future<bool> signInWithGoogle() => _run(AuthService.signInWithGoogle);

  Future<bool> signInWithFacebook() => _run(AuthService.signInWithFacebook);

  Future<void> signOut() async {
    await AuthService.signOut();
    _status = AuthStatus.signedOut;
    _error = null;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}