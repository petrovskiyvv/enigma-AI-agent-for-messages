import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiClient {
  ApiClient({required this.baseUrl});

  final String baseUrl;

  Future<dynamic> get(String path, {Map<String, String>? params}) async {
    final uri = Uri.parse('$baseUrl$path').replace(queryParameters: params);
    final response = await http.get(uri);
    return _decode(response);
  }

  Future<dynamic> post(String path, Map<String, dynamic> body) async {
    final response = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json; charset=utf-8'},
      body: json.encode(body),
    );
    return _decode(response);
  }

  Future<dynamic> patch(String path, Map<String, dynamic> body) async {
    final response = await http.patch(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json; charset=utf-8'},
      body: json.encode(body),
    );
    return _decode(response);
  }

  dynamic _decode(http.Response response) {
    return json.decode(utf8.decode(response.bodyBytes));
  }
}

import 'package:flutter/foundation.dart' show kIsWeb;

final apiClient = ApiClient(
  baseUrl: kIsWeb ? '' : 'http://127.0.0.1:8000',
);