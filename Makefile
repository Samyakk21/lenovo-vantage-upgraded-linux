.PHONY: install uninstall test

test:
	python3 -m unittest discover -s tests -v

install:
	chmod +x ./install.sh
	./install.sh 
	cp ./icon.png /usr/share/icons/hicolor/scalable/apps/vantage.png
	cp ./vantage.desktop /usr/share/applications/vantage.desktop
	cp ./vantage.sh /usr/bin/vantage
	chmod a+rx /usr/bin/vantage
	# Install CLI and Daemon
	rm -rf /usr/lib/vantage/daemon
	mkdir -p /usr/lib/vantage/daemon
	cp -r ./daemon/. /usr/lib/vantage/daemon/
	find /usr/lib/vantage/daemon -name '__pycache__' -type d -prune -exec rm -rf {} +
	find /usr/lib/vantage/daemon -name '*.pyc' -delete
	chmod +x /usr/lib/vantage/daemon/vantaged.py
	cp ./cli/vantage-cli.py /usr/bin/vantage-cli
	chmod a+rx /usr/bin/vantage-cli
	cp ./cli/vantage-gui.py /usr/bin/vantage-gui
	chmod a+rx /usr/bin/vantage-gui
	# Install D-Bus config and Systemd service
	cp ./dbus/org.lenovo.Vantage.conf /etc/dbus-1/system.d/
	cp ./systemd/vantaged.service /usr/lib/systemd/system/
	systemctl daemon-reload
	systemctl enable vantaged.service
	systemctl restart vantaged.service

uninstall:
	systemctl disable --now vantaged.service || true
	rm -f /usr/share/icons/hicolor/scalable/apps/vantage.png
	rm -f /usr/share/applications/vantage.desktop
	rm -f /usr/bin/vantage
	rm -f /usr/bin/vantage-cli
	rm -f /usr/bin/vantage-gui
	rm -rf /usr/lib/vantage
	rm -rf /etc/lenovo-vantage
	rm -f /etc/dbus-1/system.d/org.lenovo.Vantage.conf
	rm -f /usr/lib/systemd/system/vantaged.service
	systemctl daemon-reload
