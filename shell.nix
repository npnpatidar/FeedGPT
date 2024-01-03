let
  pkgs = import <nixpkgs> { };
in
pkgs.mkShell {

  packages = with pkgs;[
    figlet
    python3
    # python311Packages.pip
  ];

  shellHook = ''
    		figlet FeedGPT
    		python -m venv .venv
    		source .venv/bin/activate
    		pip install -r requirements.txt
  '';
}
