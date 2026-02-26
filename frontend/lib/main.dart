import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

void main() {
  runApp(const SupportApp());
}

class SupportApp extends StatelessWidget {
  const SupportApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Enigma Support Panel',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const TicketTableScreen(),
    );
  }
}

class TicketTableScreen extends StatefulWidget {
  const TicketTableScreen({Key? key}) : super(key: key);

  @override
  _TicketTableScreenState createState() => _TicketTableScreenState();
}

class _TicketTableScreenState extends State<TicketTableScreen> {
  List<dynamic> _tickets = [];

  @override
  void initState() {
    super.initState();
    fetchTickets();
  }

  Future<void> fetchTickets() async {
    // Обращение к нашему FastAPI бэкенду
    final response = await http.get(Uri.parse('http://127.0.0.1:8000/api/tickets'));
    if (response.statusCode == 200) {
      setState(() {
        _tickets = json.decode(utf8.decode(response.bodyBytes));
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Входящие обращения [Заготовка]')),
      body: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          columns: const [
            DataColumn(label: Text('ФИО')),
            DataColumn(label: Text('Объект')),
            DataColumn(label: Text('Суть вопроса')),
            DataColumn(label: Text('Тональность')),
          ],
          rows: _tickets.map((ticket) {
            return DataRow(cells: [
              DataCell(Text(ticket['full_name'].toString())),
              DataCell(Text(ticket['facility'].toString())),
              DataCell(Text(ticket['issue_summary'].toString())),
              DataCell(Text(ticket['emotional_tone'].toString())),
            ]);
          }).toList(),
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Заглушка для кнопки добавления записи 
          ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Функция добавления будет реализована на хакатоне')));
        },
        child: const Icon(Icons.add),
      ),
    );
  }
}