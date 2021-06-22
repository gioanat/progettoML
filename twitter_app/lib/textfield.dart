import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';

class EmojiTextfield extends StatefulWidget {
  final TextEditingController? controller;
  final String label;

  EmojiTextfield({Key? key, this.controller, required this.label})
      : super(key: key);

  @override
  _EmojiTextfieldState createState() => _EmojiTextfieldState();
}

class _EmojiTextfieldState extends State<EmojiTextfield> {
  OverlayEntry? _entry;

  late List<String> _allEmojis;

  RxList<dynamic> _filteredEmojis = RxList([]);

  RxString _filter = RxString("");

  @override
  void initState() {
    super.initState();
    _allEmojis = [
      "😉",
      "🌸",
      "😭",
      "😊",
      "💕",
      "😘",
      "😍",
      "😂",
      "❤️",
      "👍",
      "😁",
      "🙈",
      "😏",
      "🙏",
      "😱",
      "💖",
      "🔝",
      "😜",
      "💘",
      "😄",
      "💞",
      "😃",
      "👏",
      "😔",
      "💋",
      "😁",
      "♡",
      "😔",
    ];
    _filteredEmojis.addAll(_allEmojis);
  }

  _showOverlay() {
    var renderBox = context.findRenderObject() as RenderBox;
    var position = renderBox.localToGlobal(Offset.zero);
    var size = renderBox.size;

    if (_entry != null) {
      _entry!.remove();
      _entry = null;
      _filter.call("");
      return;
    }

    _entry = OverlayEntry(
      builder: (context) => Positioned(
        left: position.dx + (size.width * .60),
        top: position.dy + size.height + 5,
        child: Material(
          color: Colors.transparent,
          elevation: 5,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
          child: Container(
            width: size.width / 2,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(15),
            ),
            child: GridView.count(
              crossAxisCount: 5,
              shrinkWrap: true,
              children: _filteredEmojis
                  .map(
                    (e) => InkWell(
                      onTap: () {
                        _entry!.remove();
                        _entry = null;
                        _filter.call("");
                        var newText = widget.controller!.text + e;
                        widget.controller?.value = TextEditingValue(
                          text: newText,
                          selection: TextSelection.collapsed(
                            offset: newText.length,
                          ),
                        );
                      },
                      child: Center(child: Text(e)),
                    ),
                  )
                  .toList(),
            ),
          ),
        ),
      ),
    );
    Overlay.of(context)?.insert(_entry!);
  }

  @override
  void reassemble() {
    super.reassemble();
    _entry?.remove();
    _entry = null;
  }

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: widget.controller,
      decoration: InputDecoration(
        labelText: widget.label,
        suffixIcon: IconButton(
          icon: Icon(Icons.emoji_emotions_outlined),
          onPressed: () => _showOverlay(),
        ),
      ),
    );
  }
}
