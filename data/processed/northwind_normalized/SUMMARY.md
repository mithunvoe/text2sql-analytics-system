# Northwind Database Normalization Summary

## Normalized Tables

Total tables: 70

### categories
- Rows: 8
- Columns: 2
- Columns: category_id, description

### categories_category_id
- Rows: 8
- Columns: 4
- Columns: category_id, description, category_name, picture

### categories_category_name
- Rows: 8
- Columns: 4
- Columns: category_name, description, category_id, picture

### categories_description
- Rows: 8
- Columns: 4
- Columns: description, category_name, category_id, picture

### customer_customer_demo
- Rows: 0
- Columns: 2
- Columns: customer_id, customer_type_id

### customer_customer_demo_customer_id
- Rows: 0
- Columns: 2
- Columns: customer_id, customer_type_id

### customer_customer_demo_customer_type_id
- Rows: 0
- Columns: 2
- Columns: customer_type_id, customer_id

### customer_demographics
- Rows: 0
- Columns: 2
- Columns: customer_type_id, customer_desc

### customer_demographics_customer_desc
- Rows: 0
- Columns: 2
- Columns: customer_desc, customer_type_id

### customer_demographics_customer_type_id
- Rows: 0
- Columns: 2
- Columns: customer_type_id, customer_desc

### customers
- Rows: 91
- Columns: 2
- Columns: customer_id, phone

### customers_address
- Rows: 91
- Columns: 11
- Columns: address, company_name, country, phone, contact_title, contact_name, fax, city, postal_code, customer_id, region

### customers_city
- Rows: 69
- Columns: 3
- Columns: city, country, region

### customers_company_name
- Rows: 91
- Columns: 11
- Columns: company_name, country, phone, contact_title, contact_name, fax, address, city, postal_code, customer_id, region

### customers_contact_name
- Rows: 91
- Columns: 11
- Columns: contact_name, company_name, country, phone, contact_title, fax, address, city, postal_code, customer_id, region

### customers_customer_id
- Rows: 91
- Columns: 11
- Columns: customer_id, company_name, country, phone, contact_title, contact_name, fax, address, city, postal_code, region

### customers_phone
- Rows: 91
- Columns: 11
- Columns: phone, company_name, country, contact_title, contact_name, fax, address, city, postal_code, customer_id, region

### employee_territories
- Rows: 49
- Columns: 1
- Columns: territory_id

### employee_territories_territory_id
- Rows: 49
- Columns: 2
- Columns: territory_id, employee_id

### employees
- Rows: 9
- Columns: 4
- Columns: employee_id, notes, reports_to, photo_path

### employees_address
- Rows: 9
- Columns: 18
- Columns: address, hire_date, country, extension, photo_path, last_name, title_of_courtesy, first_name, title, reports_to, notes, employee_id, city, photo, home_phone, postal_code, region, birth_date

### employees_birth_date
- Rows: 9
- Columns: 18
- Columns: birth_date, hire_date, country, extension, photo_path, last_name, title_of_courtesy, first_name, title, reports_to, notes, address, employee_id, city, photo, home_phone, postal_code, region

### employees_city
- Rows: 5
- Columns: 4
- Columns: city, photo, country, region

### employees_country
- Rows: 2
- Columns: 3
- Columns: country, photo, region

### employees_employee_id
- Rows: 9
- Columns: 18
- Columns: employee_id, hire_date, country, extension, photo_path, last_name, title_of_courtesy, first_name, title, reports_to, notes, address, city, photo, home_phone, postal_code, region, birth_date

### employees_extension
- Rows: 9
- Columns: 18
- Columns: extension, hire_date, country, photo_path, last_name, title_of_courtesy, first_name, title, reports_to, notes, address, employee_id, city, photo, home_phone, postal_code, region, birth_date

### employees_first_name
- Rows: 9
- Columns: 18
- Columns: first_name, hire_date, country, extension, photo_path, last_name, title_of_courtesy, reports_to, title, notes, address, employee_id, city, photo, home_phone, postal_code, region, birth_date

### employees_hire_date
- Rows: 8
- Columns: 6
- Columns: hire_date, country, title_of_courtesy, city, photo, region

### employees_home_phone
- Rows: 9
- Columns: 18
- Columns: home_phone, hire_date, country, extension, photo_path, last_name, title_of_courtesy, first_name, title, reports_to, notes, address, employee_id, city, photo, postal_code, region, birth_date

### employees_last_name
- Rows: 9
- Columns: 18
- Columns: last_name, hire_date, country, extension, photo_path, title_of_courtesy, first_name, title, reports_to, notes, address, employee_id, city, photo, home_phone, postal_code, region, birth_date

### employees_notes
- Rows: 9
- Columns: 18
- Columns: notes, hire_date, country, extension, photo_path, last_name, title_of_courtesy, first_name, title, reports_to, address, employee_id, city, photo, home_phone, postal_code, region, birth_date

### employees_photo
- Rows: 1
- Columns: 2
- Columns: photo, region

### employees_photo_path
- Rows: 5
- Columns: 3
- Columns: photo_path, photo, region

### employees_postal_code
- Rows: 9
- Columns: 18
- Columns: postal_code, hire_date, country, extension, photo_path, last_name, title_of_courtesy, first_name, title, reports_to, notes, address, employee_id, city, photo, home_phone, region, birth_date

### employees_region
- Rows: 1
- Columns: 2
- Columns: region, photo

### employees_reports_to
- Rows: 2
- Columns: 3
- Columns: reports_to, photo, region

### employees_title
- Rows: 4
- Columns: 3
- Columns: title, photo, region

### employees_title_of_courtesy
- Rows: 4
- Columns: 3
- Columns: title_of_courtesy, photo, region

### order_details
- Rows: 2155
- Columns: 6
- Columns: order_details_id, order_id, product_id, unit_price, quantity, discount

### orders
- Rows: 830
- Columns: 4
- Columns: order_id, ship_name, ship_address, ship_city

### orders_customer_id
- Rows: 89
- Columns: 6
- Columns: customer_id, ship_postal_code, ship_address, ship_region, ship_country, ship_city

### orders_order_id
- Rows: 830
- Columns: 14
- Columns: order_id, ship_postal_code, ship_address, freight, order_date, ship_region, ship_city, shipped_date, ship_name, employee_id, ship_country, required_date, customer_id, ship_via

### orders_ship_address
- Rows: 89
- Columns: 6
- Columns: ship_address, ship_postal_code, ship_region, ship_city, ship_country, customer_id

### orders_ship_city
- Rows: 70
- Columns: 3
- Columns: ship_city, ship_country, ship_region

### orders_ship_name
- Rows: 90
- Columns: 7
- Columns: ship_name, ship_postal_code, ship_address, ship_region, ship_city, ship_country, customer_id

### products
- Rows: 77
- Columns: 2
- Columns: product_id, product_name

### products_product_id
- Rows: 77
- Columns: 10
- Columns: product_id, units_on_order, supplier_id, category_id, units_in_stock, discontinued, product_name, reorder_level, quantity_per_unit, unit_price

### products_product_name
- Rows: 77
- Columns: 10
- Columns: product_name, units_on_order, product_id, supplier_id, category_id, units_in_stock, discontinued, reorder_level, quantity_per_unit, unit_price

### region
- Rows: 4
- Columns: 2
- Columns: region_id, region_description

### region_region_description
- Rows: 4
- Columns: 2
- Columns: region_description, region_id

### region_region_id
- Rows: 4
- Columns: 2
- Columns: region_id, region_description

### shippers
- Rows: 6
- Columns: 2
- Columns: shipper_id, phone

### shippers_company_name
- Rows: 6
- Columns: 3
- Columns: company_name, shipper_id, phone

### shippers_phone
- Rows: 6
- Columns: 3
- Columns: phone, company_name, shipper_id

### shippers_shipper_id
- Rows: 6
- Columns: 3
- Columns: shipper_id, company_name, phone

### suppliers
- Rows: 29
- Columns: 2
- Columns: supplier_id, phone

### suppliers_address
- Rows: 29
- Columns: 12
- Columns: address, company_name, country, supplier_id, phone, contact_title, contact_name, fax, homepage, city, postal_code, region

### suppliers_city
- Rows: 29
- Columns: 12
- Columns: city, company_name, country, supplier_id, phone, contact_title, contact_name, fax, address, homepage, postal_code, region

### suppliers_company_name
- Rows: 29
- Columns: 12
- Columns: company_name, country, supplier_id, phone, contact_title, contact_name, fax, address, city, homepage, postal_code, region

### suppliers_contact_name
- Rows: 29
- Columns: 12
- Columns: contact_name, company_name, country, supplier_id, phone, contact_title, fax, address, city, homepage, postal_code, region

### suppliers_phone
- Rows: 29
- Columns: 12
- Columns: phone, company_name, country, supplier_id, contact_title, contact_name, fax, address, city, homepage, postal_code, region

### suppliers_postal_code
- Rows: 29
- Columns: 12
- Columns: postal_code, company_name, country, supplier_id, phone, contact_title, contact_name, fax, address, city, homepage, region

### suppliers_supplier_id
- Rows: 29
- Columns: 12
- Columns: supplier_id, company_name, country, phone, contact_title, contact_name, fax, address, city, homepage, postal_code, region

### territories
- Rows: 53
- Columns: 2
- Columns: territory_id, territory_description

### territories_territory_description
- Rows: 52
- Columns: 2
- Columns: territory_description, region_id

### territories_territory_id
- Rows: 53
- Columns: 3
- Columns: territory_id, territory_description, region_id

### us_states
- Rows: 51
- Columns: 2
- Columns: state_id, state_abbr

### us_states_state_abbr
- Rows: 51
- Columns: 4
- Columns: state_abbr, state_region, state_id, state_name

### us_states_state_id
- Rows: 51
- Columns: 4
- Columns: state_id, state_region, state_abbr, state_name

### us_states_state_name
- Rows: 51
- Columns: 4
- Columns: state_name, state_region, state_id, state_abbr

