import 'package:flutter/foundation.dart';

@immutable
class UserSession {
  final String id;
  final String email;
  final String fullName;
  final String role; // 'MERCHANT', 'ANALYST', 'ADMIN'
  final String status;
  final String? merchantId;
  final String? merchantName;

  const UserSession({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    required this.status,
    this.merchantId,
    this.merchantName,
  });

  factory UserSession.fromJson(Map<String, dynamic> json) {
    return UserSession(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String,
      role: (json['role'] as String).toUpperCase(),
      status: json['status'] as String? ?? 'ACTIVE',
      merchantId: json['merchant_id'] as String?,
      merchantName: json['merchant_name'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'role': role,
      'status': status,
      'merchant_id': merchantId,
      'merchant_name': merchantName,
    };
  }

  bool get isMerchant => role == 'MERCHANT';
  bool get isAnalyst => role == 'ANALYST';
  bool get isAdmin => role == 'ADMIN';

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is UserSession &&
          runtimeType == other.runtimeType &&
          id == other.id &&
          email == other.email &&
          role == other.role;

  @override
  int get hashCode => id.hashCode ^ email.hashCode ^ role.hashCode;
}
