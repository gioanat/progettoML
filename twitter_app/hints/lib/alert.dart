import 'package:flutter/material.dart';
import 'package:get/get.dart';
import 'package:hints/main.dart';
import 'package:http/http.dart' as http;

class ConfigAlert extends StatefulWidget {
  const ConfigAlert({Key? key}) : super(key: key);

  @override
  _ConfigAlertState createState() => _ConfigAlertState();
}

class _ConfigAlertState extends State<ConfigAlert> {
  late String host;
  final _formkey = GlobalKey<FormState>();
  Rx<String?> _error = null.obs;

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: Container(
        decoration: BoxDecoration(borderRadius: BorderRadius.circular(15)),
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text("Configura l'applicazione"),
            Form(
              key: _formkey,
              child: FractionallySizedBox(
                widthFactor: .4,
                child: TextFormField(
                  decoration: InputDecoration(
                    labelText: "Inserisci l'url a colab",
                  ),
                  validator: (url) {
                    if (url?.isEmpty ?? true) return "Inserisci un url";
                  },
                  onSaved: (val) => host = val!,
                ),
              ),
            ),
            Obx(
              () => _error.value == null
                  ? Container(width: 3)
                  : Text(
                      _error.value!,
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: Colors.red,
                      ),
                    ),
            ),
            Padding(
              padding: const EdgeInsets.only(top: 20),
              child: ElevatedButton(
                onPressed: () async {
                  if (_formkey.currentState?.validate() ?? false) {
                    try {
                      _formkey.currentState!.save();

                      host = host.endsWith("/") ? host : "$host/";

                      var response = await http.get(Uri.parse(host));
                      if (response.statusCode == 200) {
                        Get.back(result: Config(host: host));
                      } else {
                        Get.showSnackbar(GetBar(
                          message: "L'url immesso non è valido",
                        ));
                        _error.call("L'url immesso non è valido");
                      }
                    } catch (_) {
                      print("error in url $_");
                      Get.showSnackbar(GetBar(
                        message: "L'url immesso non è valido",
                      ));
                      _error.call("L'url immesso non è valido");
                    }
                  }
                },
                child: Text("Conferma"),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
