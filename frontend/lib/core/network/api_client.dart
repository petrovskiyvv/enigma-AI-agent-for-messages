import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
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

  Future<dynamic> delete(String path) async {
    final response = await http.delete(Uri.parse('$baseUrl$path'));
    return _decode(response);
  }

  dynamic _decode(http.Response response) {
    if (response.statusCode >= 400) {
      final body = utf8.decode(response.bodyBytes);
      throw Exception('HTTP ${response.statusCode}: $body');
    }
    return json.decode(utf8.decode(response.bodyBytes));
  }
}

String _getBaseUrl() {
  if (kIsWeb) {
    try {
      final uri = Uri.base;
      final host = uri.host;
      final port = uri.port;
      if (port == 8080 || host != 'localhost') {
        return '';
      }
    } catch (_) {}
    return 'http://localhost:8000';
  }
  if (Platform.isAndroid) return 'http://10.0.2.2:8000';
  return 'http://localhost:8000';
}

final apiClient = ApiClient(baseUrl: _getBaseUrl());