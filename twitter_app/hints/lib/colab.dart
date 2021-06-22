import 'dart:convert';

import 'package:http/http.dart' as http;

class Colab {
  Colab._internal();
  static final Colab _instance = Colab._internal();
  factory Colab() => _instance;

  late Uri _colabUri;

  set colabUri(String url) => this._colabUri = Uri.parse(url);

  Future<List<String>> generateTweet(String? seed) async {
    var tweets = await http.post(
      Uri.parse(_colabUri.toString() + "/generateTweet"),
      body: {"seed": seed},
      headers: {"ContentType": "application/json"},
    );

    return (jsonDecode(tweets.body) as List).map((e) => e.toString()).toList();
  }

  Future<List<String>> generateSingleWord(String? seed) async {
    var words = await http.post(
      Uri.parse(_colabUri.toString() + "/generateWords"),
      body: {"seed": seed},
      headers: {"ContentType": "application/json"},
    );

    return (jsonDecode(words.body) as List).map((e) => e.toString()).toList();
  }

  Future<String> translate(String? seed) async {
    var translation = await http.post(
      Uri.parse(_colabUri.toString() + "/generateWord"),
      body: {"seed": seed},
      headers: {"ContentType": "application/json"},
    );

    return translation.body;
  }
}
