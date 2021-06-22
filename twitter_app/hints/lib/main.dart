import 'dart:async';

import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:hints/alert.dart';
import 'package:hints/colab.dart';
import 'package:hints/hint_card.dart';
import 'package:hints/textfield.dart';

void main() => runApp(GetMaterialApp(home: MyApp()));

class Config {
  String host;

  Config({required this.host});
}

class MyApp extends StatefulWidget {
  MyApp({Key? key}) : super(key: key);

  @override
  _MyAppState createState() => _MyAppState();
}

/// Debounce 2s prima di generare word
/// btn -> generate twwe

class _MyAppState extends State<MyApp> {
  late final Colab _colab;
  final RxList<String> _hints = RxList();
  final _controller = TextEditingController();

  final RxMap<int, bool> _expandedTile = {-1: false}.obs;

  @override
  void initState() {
    super.initState();
    _colab = Colab();
    Future.delayed(Duration(milliseconds: 10), () => _init());
    _expandedTile.listen((val) => print(val));
  }

  _init() async {
    showDialog<Config>(
      context: context,
      barrierDismissible: false,
      builder: (context) => ConfigAlert(),
    ).then((value) {
      if (value != null) _colab.colabUri = value.host;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          onPressed: () => _init(),
          icon: Icon(Icons.logout),
        ),
      ),
      body: Container(
        child: Row(
          children: [
            Expanded(
              flex: 2,
              child: Column(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                    child: EmojiTextfield(
                      label: "Inserisci un inizio di tweet",
                      controller: _controller,
                    ),
                  ),
                  Padding(
                    padding:
                        const EdgeInsets.symmetric(vertical: 20, horizontal: 5),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        Expanded(
                          child: ElevatedButton(
                            onPressed: () => Colab()
                                .generateTweet(_controller.text)
                                .then((value) => _hints
                                  ..clear()
                                  ..addAll(value)),
                            child: Text("Genera frase"),
                          ),
                        ),
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.only(left: 5),
                            child: ElevatedButton(
                              onPressed: () => Colab()
                                  .translate(_controller.text)
                                  .then((value) => _hints
                                    ..clear()
                                    ..add(value)),
                              child: Text("Traduci"),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  Divider(),
                  Expanded(
                    child: Obx(
                      () => ListView(
                        physics: AlwaysScrollableScrollPhysics(),
                        children: _hints
                            .map((item) => HintCard(
                                content: item, controller: _controller))
                            .toList(),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: Align(
                alignment: Alignment.topRight,
                child: Container(
                  child: Image.asset("assets/alberto.png"),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
