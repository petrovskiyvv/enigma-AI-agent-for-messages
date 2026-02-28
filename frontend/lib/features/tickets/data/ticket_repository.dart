import '../../../core/network/api_client.dart';
import '../domain/ticket.dart';

class TicketRepository {
  const TicketRepository(this._client);

  final ApiClient _client;

  Future<List<Ticket>> fetchAll({
    String? status,
    String? tone,
    String? search,
  }) async {
    final params = <String, String>{
      if (status != null) 'status': status,
      if (tone != null) 'tone': tone,
      if (search != null && search.isNotEmpty) 'search': search,
    };
    final data = await _client.get('/api/tickets', params: params) as List;
    return data.map((e) => Ticket.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Ticket> create(Map<String, String> fields) async {
    final data = await _client.post('/api/tickets', fields);
    return Ticket.fromJson(data as Map<String, dynamic>);
  }

  Future<Ticket> update(int id, {String? aiResponse, String? status}) async {
    final data = await _client.patch('/api/tickets/$id', {
      if (aiResponse != null) 'ai_response': aiResponse,
      if (status != null) 'status': status,
    });
    return Ticket.fromJson(data as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> fetchStats() async {
    return (await _client.get('/api/stats')) as Map<String, dynamic>;
  }
}

final ticketRepository = TicketRepository(apiClient);