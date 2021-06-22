import 'package:flutter/material.dart';

class HintCard extends StatelessWidget {
  final String content;
  final TextEditingController controller;

  HintCard({
    Key? key,
    required this.content,
    required this.controller,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      child: ExpansionTile(
        title: Text(content),
        initiallyExpanded: false,
        trailing: Icon(Icons.translate_outlined),
        children: [
          Divider(),
          ListTile(
            title: Text(content),
          )
        ],
      ),
    );
  }
}
