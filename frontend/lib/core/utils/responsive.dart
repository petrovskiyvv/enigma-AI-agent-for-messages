import 'package:flutter/material.dart';

// Всё что уже экрана планшета считается мобильным
bool isMobile(BuildContext context) =>
    MediaQuery.of(context).size.width < 600;
