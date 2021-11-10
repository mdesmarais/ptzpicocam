PTZ Pico camera
===============

Ce projet est constitué de deux applications :

* **ptzpicocam** : application destinée à être exécutée sur un Raspberry PI Pico pour contrôler une caméra
* **ptzsimcam** : simulation d'une caméra ptz contrôlable via une interface graphique ou via le port série

Une caméra PTZ est pilotable sur trois axes : horizontal (Pan), vertical (Tilt) et la profondeur (zoom). Le modèle de référence est la caméra EVI-H100s de Sony. Elle peut être contrôlé via un port série en utilisant le protocole `visca <https://pro.sony/support/res/manuals/AE4U/AE4U1001M.pdf>`_.

L'application **ptzpicocam** est écrit en Micropython. Les tests unitaires associés sont destinés à être exécutés en python sur un ordinateur.

Un simulateur a été développé pour pouvoir tester l'implémentation de ce protocole sans avoir besoin de matériel. Il est écrit en python et est basé sur `pybullet <https://pybullet.org/wordpress/>`_. La caméra a été modélisé avec le langage URDF pour être reconnu par la simulation. Elle est contrôlable via une interface graphique ou via le port série. Cette dernière option permet d'utiliser du vrai matériel pour piloter la caméra.

Dépendances
-----------

Le simulateur a été testé avec Python 3.8. Les versions 3.7+ devraient fonctionner.

* numpy v1.21.3
* pybullet v3.2.0
* pyserial v3.5
* scipy v1.7.1


Installation
------------

L'utilisation d'un environnement virtuel est conseillé pour éviter des conflits de dépendances. La création d'un environnement peut se faire avec l'outil `venv <https://docs.python.org/3/library/venv.html>`_. Après avoir installé l'outil, il faudra saisir la commande suivante :code:`python3 -m venv env`. L'environnement devra être activé à chaque ouverture du terminal avec la commande suivante :

* Linux : :code:`source env/bin/activate`
* Windows : :code:`env\Scripts\activate.bat`

L'installation du simulateur se fait en utilisant le script setup.py : :code:`python3 setup.py install`. Les dépendances seront automatiquement installées.

Utilisation
-----------

Le lancement du simulateur se fait avec la commande **ptzsim**. Par defaut la simulation est uniquement contrôlable via l'interface graphique. En passant l'argument :code:`--serial`, la caméra peut être contrôlée via le port série.

Exemple : :code:`ptzsim --serial /dev/ttyACM0`.

Tests
-----

Les tests peuvent être exécutées avec pytest.
