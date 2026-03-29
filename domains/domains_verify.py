import socket


def is_valid_domain(domain):
    try:
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        return False


def check_domains(file_path):
    invalid_domains = []

    with open(file_path, "r") as f:
        domains = [line.strip() for line in f if line.strip()]

    for domain in domains:
        if not is_valid_domain(domain):
            print(f"Invalid: {domain}")
            invalid_domains.append(domain)

    print("\nSummary:")
    print(f"Total checked: {len(domains)}")
    print(f"Invalid domains: {len(invalid_domains)}")


if __name__ == "__main__":
    check_domains("domains_all")
