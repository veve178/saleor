from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
import requests

from ....interface import AddressData, PaymentLineData


@pytest.fixture
def dummy_payment_line_data():
    return [
        PaymentLineData(
            gross=Decimal("100.00"),
            product_name="Product Name",
            product_sku="PRODUCT_SKU123",
            quantity=5,
        )
    ] * 3


@pytest.fixture
def np_payment_data(dummy_payment_data, dummy_payment_line_data):
    address_data = AddressData(
        first_name="John",
        last_name="Doe",
        company_name="",
        phone="+81 03-1234-5678",
        country="JP",
        postal_code="370-2625",
        country_area="群馬県",
        city="甘楽郡下仁田町",
        city_area="本宿",
        street_address_1="2-16-3",
        street_address_2="",
    )
    dummy_payment_data.billing = address_data
    dummy_payment_data.shipping = address_data
    dummy_payment_data.lines = dummy_payment_line_data
    return dummy_payment_data


@patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_process_payment_authorized(
    mocked_request, np_atobarai_plugin, np_payment_data
):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(
            return_value={
                "results": [
                    {
                        "shop_transaction_id": "abc1234567890",
                        "np_transaction_id": "18121200001",
                        "authori_result": "00",
                        "authori_required_date": "2018-12-12T12:00:00+09:00",
                    }
                ]
            }
        ),
    )
    mocked_request.return_value = response

    # when
    gateway_response = plugin.process_payment(payment_data, None)

    # then
    assert gateway_response.is_success
    assert not gateway_response.error


@patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_process_payment_refused(mocked_request, np_atobarai_plugin, np_payment_data):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    response = Mock(
        spec=requests.Response,
        status_code=200,
        json=Mock(
            return_value={
                "results": [
                    {
                        "shop_transaction_id": "abc1234567890",
                        "np_transaction_id": "18121200001",
                        "authori_result": "20",
                        "authori_required_date": "2018-12-12T12:00:00+09:00",
                    }
                ]
            }
        ),
    )
    mocked_request.return_value = response

    # when
    gateway_response = plugin.process_payment(payment_data, None)

    # then
    assert not gateway_response.is_success


@patch("saleor.payment.gateways.np_atobarai.api.requests.request")
def test_process_payment_error(mocked_request, np_atobarai_plugin, np_payment_data):
    # given
    plugin = np_atobarai_plugin()
    payment_data = np_payment_data
    response = Mock(
        spec=requests.Response,
        status_code=400,
        json=Mock(return_value={"errors": [{"codes": ["E0100059", "E0100083"]}]}),
    )
    mocked_request.return_value = response

    # when
    gateway_response = plugin.process_payment(payment_data, None)

    # then
    assert not gateway_response.is_success
    assert (
        "Please check if the customer’s ZIP code and address match."
        in gateway_response.error
    )
    assert (
        "Please make sure the delivery destination (ZIP code) and address match."
        in gateway_response.error
    )
