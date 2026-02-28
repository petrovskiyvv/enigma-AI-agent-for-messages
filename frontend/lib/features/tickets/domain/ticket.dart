class Ticket {
  const Ticket({
    required this.id,
    required this.createdAt,
    required this.fullName,
    required this.facility,
    required this.phone,
    required this.email,
    required this.deviceNumbers,
    required this.deviceType,
    required this.emotionalTone,
    required this.category,
    required this.issueSummary,
    required this.originalText,
    required this.aiResponse,
    required this.status,
  });

  final int id;
  final String createdAt;
  final String fullName;
  final String facility;
  final String phone;
  final String email;
  final String deviceNumbers;
  final String deviceType;
  final String emotionalTone;
  final String category;
  final String issueSummary;
  final String originalText;
  final String aiResponse;
  final String status;

  factory Ticket.fromJson(Map<String, dynamic> json) => Ticket(
        id: json['id'] as int,
        createdAt: json['created_at'] as String? ?? '',
        fullName: json['full_name'] as String? ?? '',
        facility: json['facility'] as String? ?? '',
        phone: json['phone'] as String? ?? '',
        email: json['email'] as String? ?? '',
        deviceNumbers: json['device_numbers'] as String? ?? '',
        deviceType: json['device_type'] as String? ?? '',
        emotionalTone: json['emotional_tone'] as String? ?? 'Нейтрально',
        category: json['category'] as String? ?? '',
        issueSummary: json['issue_summary'] as String? ?? '',
        originalText: json['original_text'] as String? ?? '',
        aiResponse: json['ai_response'] as String? ?? '',
        status: json['status'] as String? ?? 'Новое',
      );

  Ticket copyWith({String? aiResponse, String? status}) => Ticket(
        id: id,
        createdAt: createdAt,
        fullName: fullName,
        facility: facility,
        phone: phone,
        email: email,
        deviceNumbers: deviceNumbers,
        deviceType: deviceType,
        emotionalTone: emotionalTone,
        category: category,
        issueSummary: issueSummary,
        originalText: originalText,
        aiResponse: aiResponse ?? this.aiResponse,
        status: status ?? this.status,
      );
}
